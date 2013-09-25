#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Management of the templates.

The templates are sample files used to create quickly a napixd manager.
The source templates are file in the same directory as this file.

They are generated in the :file:`HOME/auto/` directory.

"""

import os
import sys
import optparse

from napixd import get_path, get_file

TEMPLATE_DIR = os.path.dirname(__file__)
SUFFIX = '.py.templ'


def copy_template(name, template):
    """
    Copy the template named *template* into a destination file *name*.

    *name* is the complete file name without path components.
    *template* is the template name without path nor suffix.
    """
    path = get_file(os.path.join('auto', name))
    orig = os.path.join(TEMPLATE_DIR, template + SUFFIX)

    with open(path, 'w') as dst:
        with open(orig, 'r') as src:
            for line in src:
                dst.write(line)

    return path


def list_templates():
    """
    Returns a list of templates names.
    """
    suffix_len = len(SUFFIX)
    return [d[:-suffix_len] for d in os.listdir(TEMPLATE_DIR)
            if not d.startswith('.') and d.endswith(SUFFIX)]


def get_template_name(name):
    """
    Find a unique template name starting with *name*
    """
    name = name.lower()
    file_name = '{0}.py'.format(name)
    i = 0
    auto_dir = get_path('auto')
    while os.path.exists(os.path.join(auto_dir, file_name)):
        i += 1
        file_name = '{0}_{1}.py'.format(name, i)

    return file_name


def run():
    """
    Parse the :data:`sys.argv` and run the commands.
    """
    parser = optparse.OptionParser(
        usage='usage: %prog -l|--list\n %prog [-n|--name destination] template_name'
    )
    parser.add_option('-l', '--list',
                      help='List the templates',
                      action='store_true',
                      default=False)
    parser.add_option('-n', '--name',
                      help='Name of the destination',
                      default='my_manager')
    options, args = parser.parse_args()

    if options.list:
        sys.stdout.write('\n'.join(sorted(list_templates())))
        sys.stdout.write('\n')
        return 0

    if len(args) != 1:
        template, = args
    else:
        template = 'default'

    if template not in list_templates():
        sys.stderr.write('Template {0} does not exists'.format(template))
        return 1

    dest = get_template_name(options.name)
    path = copy_template(dest, template)

    sys.stdout.write('Template generated in {0}\n'.format(path))
    return 0
