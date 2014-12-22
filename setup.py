#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


def get_version():
    """Gets the repository version."""
    import subprocess
    proc = subprocess.Popen('hg log -r tip --template "{latesttagdistance}"',
                            shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pending, _ = proc.communicate()
    return "%(pending)s" % dict(pending=pending)


setup(name='strappo-api',
      version=get_version(),
      packages=['app'],
      install_requires=[
          'gunicorn==19.1.1',
          'weblib',
          'strappon'
      ])
