#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from setuptools import find_packages
from setuptools import setup

from app import get_name
from app import get_version


requirements = os.path.join(os.path.dirname(__file__), 'requirements.txt')
INSTALL_REQUIRES = open(requirements).read().split()


params = dict(
    name=get_name(),
    version=get_version(),
    packages=find_packages(exclude=['fabfile']),
    install_requires=INSTALL_REQUIRES,
)

setup(**params)
