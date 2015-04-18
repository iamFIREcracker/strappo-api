#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weblib import internalerror

from app import app_factory


app = app_factory()
app.internalerror = internalerror('Holy shit!')

app = app.wsgifunc()
