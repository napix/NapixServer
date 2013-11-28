#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="napixd",
    version="1.6",
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
        'napix>=0.6',
    ],
    include_package_data=True,
    scripts=[
        'bin/napixd'
    ],
    dependency_links=[
        'http://builds.enix.org/napix/napix-latest.tar.gz#egg=napix-9999',
    ],
)
