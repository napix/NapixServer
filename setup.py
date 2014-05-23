#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from setuptools import find_packages, setup


def find_version(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath) as init:
        for line in init:
            if line.startswith('__version__'):
                x, version = line.split('=', 1)
                return version.strip().strip('\'"')
        else:
            raise ValueError('Cannot find the version in {0}'.format(filename))


def parse_requirements(requirements_txt):
    requirements = []
    try:
        with open(requirements_txt, 'rb') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if line.startswith('-'):
                    raise ValueError('Unexpected command {0} in {1}'.format(
                        line,
                        requirements_txt,
                    ))

                requirements.append(line)
        return requirements
    except IOError:
        return []


build_info = dict(
    name='napixd',
    version=find_version('napixd/__init__.py'),
    packages=find_packages(
        exclude=[
            'napixd.examples',
            'tests',
            'tests.*',
        ]
    ),
    url='http://napix.io',
    author='Enix',
    author_email='gr@enix.org',
    install_requires=parse_requirements('requirements.txt'),
    include_package_data=True,
    scripts=[
        'bin/napixd',
        'bin/napixd-template',
        'bin/napixd-store',
    ],
)


if __name__ == '__main__':
    setup(**build_info)
