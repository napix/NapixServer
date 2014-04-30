#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def find_version(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath) as init:
        for line in init:
            if line.startswith('__version__'):
                x, version = line.split('=', 1)
                return version.strip().strip('\'"')
        else:
            raise ValueError('Cannot find the version in {0}'.format(filename))

setup(
    name="napixd",
    version=find_version('napixd/__init__.py'),
    packages=find_packages(
        exclude=[
            'napixd.examples',
            'tests',
            'tests.*',
        ]
    ),
    author='Enix',
    author_email='gr@enix.org',
    install_requires=[
    ],
    extra_require={
        'base': [
            'dotconf',
            'permissions',
            'napix',
        ],
        'production': [
            'napixd[base]',
            'gevent',
        ],
    },
    include_package_data=True,
    scripts=[
        'bin/napixd',
        'bin/napixd-template',
        'bin/napixd-store',
    ],
    dependency_links=[
    ],
)
