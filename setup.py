#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="napixd",
    version="1.3",
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
        'bottle>=0.11',
        'permissions>=1.4',
        'napix>=0.6',
    ],
    include_package_data=True,
    scripts=[
        'bin/napixd'
    ],
    dependency_links=[
        'http://builds.enix.org/napix/permissions-latest.tar.gz#egg=permissions-9999',
        'http://builds.enix.org/napix/napix-latest.tar.gz#egg=napix-9999',
    ],
)
