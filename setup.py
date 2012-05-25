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
        ('napixd/web', [ 'napixd/web/index.html' ]),
        ('napixd/web/help', [
            'napixd/web/help/executor.html',
            'napixd/web/help/deploy.html',
            'napixd/web/help/low_level.html',
            'napixd/web/help/high_level.html'
            ]),
        ('napixd/web/css', [
            'napixd/web/css/index.css',
            'napixd/web/css/help.css'
            ]),
        ('napixd/web/js', [
            'napixd/web/js/firstrun.js',
            'napixd/web/js/main.js'
            ]),
        ('napixd/web/js/libs', [
            'napixd/web/js/libs/require.js'
            ]),
        ('napixd/web/img', [
            'napixd/web/img/glyphicons-halflings-white.png',
            'napixd/web/img/glyphicons-halflings.png'
            ]),
        ]
    )
