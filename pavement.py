#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import optparse

from tarfile import TarFile
try:
    import requests
except ImportError:
    requests = None

from paver.easy import task, needs, cmdopts, options, path, call_task, sh
from paver.setuputils import setup

try:
    from setup import build_info
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from setup import build_info


setup(**build_info)
is_prerelease = (
    'a' in options.setup.version or
    'b' in options.setup.version or
    'rc' in options.setup.version
)


@task
def clean():
    """Clean the workspace"""
    path('dist').rmtree()


@task
@needs(['clean', 'web', 'distutils.command.sdist'])
@cmdopts([
    ('web_archive=', 'w', 'Web site package')
], share_with=['web'])
def make(options):
    """Overrides sdist to make sure that our setup.py is generated."""
    if not is_prerelease:
        target = '{name}-{version}.tar.gz'.format(**options.setup)
        link = 'dist/{name}-latest.tar.gz'.format(**options.setup)
        sys.stderr.write('Link {0} to {1}\n'.format(link, target))
        path(target).symlink(link)


@task
def test_archive():
    if path('archive-test').isdir():
        path('archive-test').rmtree()

    target = 'dist/{name}-{version}.tar.gz'.format(**options.setup)
    sh(['virtualenv', '--python', 'python2', 'archive-test'])
    sh(['archive-test/bin/pip', 'install', target])
    sh(['archive-test/bin/napixd', 'only'])


remote_archive = 'http://builds.napix.io/web/napix-latest.tar.gz'


@task
@cmdopts([
    ('web_archive=', 'w', 'Web site package'),
])
def web(options):
    """Extracts a web archive in the web directory"""
    web_archive = getattr(options.web, 'web_archive', remote_archive)

    if '://' in web_archive:
        if requests is None:
            raise ValueError('Missing required lib requests')
        url = web_archive
        web_archive = path(web_archive).basename()
        sys.stderr.write('Downloading from {0} to {1}\n'.format(url, web_archive))
        dl = requests.get(url)

        chunk_size = 4 * 2**10
        with open(web_archive, 'wb') as fd:
            for chunk in dl.iter_content(chunk_size):
                fd.write(chunk)

    path('napixd/web').rmtree()
    tf = TarFile.open(web_archive)

    for ti in tf.getmembers():
        name = path(ti.name)
        if name.basename() == 'index.html':
            web_root = name.dirname()
            break
    else:
        raise ValueError('Missing index.html')

    tf.extractall('temp/')
    tf.close()

    path(os.path.join('temp', web_root)).move('napixd/web')
    path('temp').rmdir()


@task
@cmdopts([
    ('output=', 'o', 'Output of the flake8 report'),
])
def flake8(options):
    """Enforces PEP8"""
    out = getattr(options.flake8, 'output', '-')
    flake8_command = ['flake8', '--max-line-length=120', '--exit-zero']
    flake8_command.extend(package for package in options.setup['packages'] if '.' not in package)
    flake8_report = sh(flake8_command, capture=True)

    if out == '-':
        outfile = sys.stdout
    else:
        outfile = open(out, 'wb')

    try:
        outfile.write(flake8_report)
    finally:
        if outfile is not sys.stdout:
            outfile.close()


def _nosetests(options):
    nosetest_options = {}

    if hasattr(options, 'xunit'):
        nosetest_options.update({
            'with-xunit': True,
            'xunit-file': options.xunit,
            'verbosity': '0',
        })

    if hasattr(options, 'auto'):
        tests = [
            ('tests.' + '.'.join('test_{0}'.format(test) for test in auto.split('.')[1:]))
            for auto in options.auto]
    elif hasattr(options, 'test'):
        tests = options.test
    else:
        tests = ['tests']

    nosetest_options['tests'] = tests
    return nosetest_options


@task
@cmdopts([
    optparse.make_option('-t', '--test',
                         action='append',
                         help='Select the test to run'),
    optparse.make_option('-a', '--auto',
                         action='append',
                         metavar='PACKAGE',
                         help='Automatically select the test from a package'),
    optparse.make_option('-x', '--xunit',
                         metavar='COVERAGE_XML_FILE',
                         help='Export a xunit file'),
])
def test(options):
    """Runs the tests"""
    return call_task('nosetests', options=_nosetests(options.test))


@task
@cmdopts([
    optparse.make_option('-c', '--packages',
                         action='append',
                         help='Select the packages to cover'),
    optparse.make_option('-t', '--test',
                         action='append',
                         help='Select the test to run'),
    optparse.make_option('-a', '--auto',
                         action='append',
                         metavar='PACKAGE',
                         help='Automatically select the test and the package to cover'),
    optparse.make_option('-x', '--xunit',
                         metavar='XUNIT_FILE',
                         help='Export a xunit file'),
    optparse.make_option('-g', '--xcoverage',
                         metavar='COVERAGE_XML_FILE',
                         help='Export a cobertura file'),
])
def coverage(options):
    """Runs the unit tests and compute the coverage"""

    nosetest_options = _nosetests(options.coverage)
    nosetest_options.update({
        'cover-erase': True,
    })

    if hasattr(options.coverage, 'xcoverage'):
        nosetest_options.update({
            'with-xcoverage': True,
            'xcoverage-file': options.coverage.xcoverage,
            'xcoverage-to-stdout': False,
        })
    else:
        nosetest_options.update({
            'with-coverage': True,
        })

    if hasattr(options.coverage, 'auto'):
        packages = options.coverage.auto
    elif hasattr(options.coverage, 'packages'):
        packages = options.coverage.packages
    else:
        packages = list(set(x.split('.')[0] for x in options.setup.get('packages')))

    nosetest_options.update({
        'cover-package': packages,
    })

    return call_task('nosetests', options=nosetest_options)


@task
def jenkins():
    """Runs the Jenkins tasks"""
    # Generate nosetest.xml
    # Generate coverage.xml
    # Generate flake8.log

    call_task('flake8', options={
        'output': 'flake8.log',
    })
    call_task('coverage', options={
        'xunit': 'nosetests.xml',
        'xcoverage': 'coverage.xml',
    })


@task
def push():
    """Pushes the archive in the enix repo"""
    call_task('distutils.command.sdist')
    call_task('upload', options={
        'repository': 'http://enixpi.enix.org',
    })
