#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import web
from werkzeug.debug import DebuggedApplication

from app import app_factory


app = app_factory()

if web.config.debug:
    def nointernalerror():
        raise sys.exc_info()
    app.internalerror = nointernalerror

    app = DebuggedApplication(app.wsgifunc(), evalex=True)
else:
    app = app.wsgifunc()
