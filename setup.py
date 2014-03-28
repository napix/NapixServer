#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="napixd",
    version="1.8.0b",
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
