#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app.config


def get_name():
    """Gets the name of the application."""
    return app.config.APP_NAME


def get_version():
    """Gets the repository version."""
    import subprocess
    proc = subprocess.Popen(
            'hg log -r tip --template "{latesttagdistance}"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pending, _ = proc.communicate()
    return "%(tag)sd%(pending)s" % dict(tag=app.config.TAG, pending=pending)

