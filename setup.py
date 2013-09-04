#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
        name="napixd",
        version="0.7",
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
            'permissions>=0.1',
            ],
        include_package_data=True,
        scripts=[
            'bin/napixd'
            ],
        dependency_links=[
            'http://builds.enix.org/napix/permissions-latest.tar.gz#egg=permissions-0.1',
            ],
        )
