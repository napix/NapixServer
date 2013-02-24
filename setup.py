#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name="napixd",
        version="0.2",
        packages=find_packages(
            exclude=[
                'napixd.examples',
                'tests',
                'tests.*',
                ]),
    install_requires=[
        'bottle>=0.11',
        'gevent>0.99',
        ],
    scripts=[
        'bin/napixd'
        ],
    )
