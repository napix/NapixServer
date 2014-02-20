#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="napixd",
    version="1.6.7",
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
    extra_requires={
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
        'bin/napixd'
    ],
    dependency_links=[
    ],
)
