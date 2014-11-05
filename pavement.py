#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import optparse

try:
    import requests
except ImportError:
    requests = None

from paver.easy import task, needs, cmdopts, path, call_task, no_help

try:
    from setup import build_info
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from setup import build_info


import sett


@task
@no_help
@cmdopts([
    optparse.make_option('-n', '--naked',
                         action='store_true',
                         default=False,
                         help='Create a package with minimal dependencies'),
])
def setup_options(options):
    nodeps = getattr(getattr(options, 'setup_options', None), 'naked', False)

    sys.stderr.write('Creating {0} version\n'.format(
        'nodeps' if nodeps else 'standard'
    ))
    if nodeps:
        build_info['name'] += '-nodeps'
    call_task('sett.build.setup_options')


@task
@no_help
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-n', '--naked',
                         action='store_true',
                         default=False,
                         help='Create a package with minimal dependencies'),
])
def set_requirements(options):
    path('requirements.txt').unlink_p()
    if options.set_requirements.naked:
        path('naked_requirements.txt').copy('requirements.txt')
    else:
        path('default_requirements.txt').copy('requirements.txt')


@task
@needs(['web', 'set_requirements'])
@cmdopts([], share_with=['set_requirements', 'setup_options'])
def make(options):
    """Overrides sdist to make sure that our setup.py is generated."""
    call_task('sett.build.make')


remote_archive = 'http://builds.napix.io/web/napix-latest.tar.gz'


@task
@cmdopts([
    ('web_archive=', 'w', 'Web site package'),
])
def web(options):
    web_archive = getattr(options.web, 'web_archive', remote_archive)
    call_task('install_remote_tar', args=[web_archive, 'napixd/web'])
