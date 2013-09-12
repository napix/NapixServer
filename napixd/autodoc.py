#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
import os
import napixd
from napixd.managers import Manager

try:
    from sphinx.application import Sphinx
except ImportError, e:
    Sphinx = None

logger = logging.getLogger('Napix.autodoc')


class Story(object):

    def __init__(self):
        self._story = []
        self._indent = 0

    def __unicode__(self):
        return '\n'.join(self._story)

    def append_title(self, string, *args, **kwargs):
        level = kwargs.pop('level', '=')
        if kwargs:
            raise TypeError, 'Got unexpected keywork arguments : %s' % ','.join(
                kwargs.keys())
        title = string % args
        self._story.append(title)
        self._story.append(level * len(title))
        self._story.append('')

    def append(self, string, *args):
        if string:
            if args:
                string = string % args
        else:
            string = ''
        indent = '\t' * self._indent
        for chunck in map(str.strip, string.split('\n')):
            if chunck:
                self._story.append(indent + chunck)
        self._story.append('')

    def append_py(self, py, name):
        self._append_py(py, name)
        self._story.append('')

    def _append_py(self, py, name):
        self._append('.. py:%s:: %s' % (py, name))

    def _append(self, string):
        self._story.append('\t' * self._indent + string)

    def indent(self):
        self._indent += 1

    def unindent(self):
        self._indent -= 1

    @contextmanager
    def indentation(self):
        self.indent()
        yield
        self.unindent()

    def write(self, fd):
        fd.write('\n'.join(self._story))

    def append_method(self, method, signature, return_type):
        self._append_py('method', method +
                        ('(%s)' % signature if signature else '') +
                        (' -> %s' % return_type if return_type else ''))
        self._story.append('')
        return self.indentation()


class Autodocument(object):
    directory = napixd.get_path('doc')

    def generate_doc(self, managers):
        outdir = os.path.join(self.directory, 'build')
        logger.info('Generating documentation in %s', self.directory)
        for alias, manager in managers:
            self.make_documentation(alias, manager)

        if not Sphinx:
            logger.warning('Sphinx is not installed, doc is not generated')
            return

        sphinx = Sphinx(
            srcdir=self.directory,
            doctreedir=os.path.join(self.directory, 'doctrees'),
            outdir=outdir,
            confdir=self.directory,
            buildername='html',
            warning=open('/dev/null', 'w'),
            status=open('/dev/null', 'w'),
        )
        sphinx.build()
        return outdir

    def make_documentation(self, alias, manager):
        doc_file_path = os.path.join(
            self.directory, manager.__module__ + '.rst')
        logger.debug('Start dumping doc of %s to %s',
                     manager.get_name(), doc_file_path)
        try:
            handle = open(doc_file_path, 'wb')
        except IOError as e:
            logger.error(
                'Failed to write %s, because of %s', doc_file_path, str(e))
            raise
        body = Story()
        body.append_py('module', manager.__module__)
        self._document(manager, body)
        body.write(handle)
        handle.close()

    def _document(self, manager, body):
        name = manager.get_name()

        body.append_title(name)

        body.append_py('class', manager.__name__)
        body.indent()
        body.append(manager.__doc__)

        if manager.get_managed_classes():
            body.append_py(' attribute', 'managed_class')
            for mgr in manager.get_managed_classes():
                with body.indentation():
                    body.append(':py:class:`%s`' % mgr.__name__)

        if manager.detect != Manager.detect:
            body.append_py('classmethod', 'detect')
            with body.indentation():
                body.append(manager.detect.__doc__)

        for field, metadatas in manager.resource_fields.items():
            body.append_py('attribute', field)
            with body.indentation():
                if 'example' in metadatas:
                    body.append(':Example: %s', metadatas['example'])
                body.append(metadatas.get('description', '!!No description'))

        for action in manager.get_all_actions():
            body.append_py('method', action.__name__)
            with body.indentation():
                body.append(metadatas.get('description', '!!No description'))

        all_implemented_methods = set(
            method for method in dir(manager) if method[0] != '_')

        manager_interface = {
            'get_resource': ('resource_id', 'resource_dict'),
            'list_resource': ('', 'list of resource_id'),
            'create_resource': ('resource_dict', 'resource_id'),
            'modify_resource': ('resource_id, resource_dict', 'resource_id'),
            'delete_resource': ('resource_id', '')
        }

        for method in all_implemented_methods.intersection(manager_interface.iterkeys()):
            signature, return_type = manager_interface[method]
            with body.append_method(method, signature, return_type):
                body.append(getattr(manager, method).__doc__)

        validate_methods = {
            'validate_resource': ('resource_dict', 'Check the validity of the resource'),
            'validate_id': ('resource_id', 'Check the validity of an ID')
        }
        for field in manager.resource_fields:
            validate_methods['validate_resource_' + field] = (
                field, 'Check the validity of `%s` field' % field)

        for method_name in all_implemented_methods.intersection(validate_methods):
            method = getattr(manager, method_name)
            if method == getattr(Manager, method_name, None):
                continue
            field, default = validate_methods[method_name]
            with body.append_method(method_name, field, field):
                body.append(method.__doc__ or default)

        body.unindent()

        for child_manager in manager.get_managed_classes():
            if child_manager.__module__ == manager.__module__:
                self._document(child_manager, body)
