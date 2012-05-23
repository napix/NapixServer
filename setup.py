#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

def find_data(root_dir):
    return sum([
        [os.path.join(dirname, filename)
            for filename in filelist]
        for dirname, dirlist, filelist
        in os.walk(root_dir)], [])

setup(name="napixd",
        version="0.1",
        packages=find_packages(),
    install_requires=[
        'bottle==0.10.8',
        'httplib2==0.7.4',
        'Rocket==1.2.4',
        ],
    scripts=[
        'bin/napixd'
        ],
    data_files=[
        ('napixd/conf', ['napixd/conf/settings.json']),
        ('napixd/web', find_data('napixd/web')),
        ],
        )
