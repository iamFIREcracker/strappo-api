#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers.drivers import DriversController


URLS = (
    '/1/drivers', DriversController,
) + (() if not web.config.DEV else (
    # Develop routes
))
