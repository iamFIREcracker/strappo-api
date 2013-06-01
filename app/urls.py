#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import HelloHandler


URLS = (
    '/hello', HelloHandler,
) + (() if not web.config.DEV else (
    # Develop routes
))
