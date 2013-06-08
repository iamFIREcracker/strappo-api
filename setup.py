#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from setuptools import find_packages
from setuptools import setup


def get_version():
    """Gets the repository version."""
    import subprocess
    proc = subprocess.Popen(
            'hg log -r tip --template "{latesttagdistance}"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pending, _ = proc.communicate()
    return "%(tag)sd%(pending)s" % dict(tag='0.0.1', pending=pending)


requirements = os.path.join(os.path.dirname(__file__), 'requirements.txt')
INSTALL_REQUIRES = open(requirements).read().split()


params = dict(
    name='poolit',
    version=get_version(),
    packages=find_packages(exclude=['fabfile']),
    install_requires=INSTALL_REQUIRES,
)

setup(**params)
