#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers.drivers import EditDriverController
from app.controllers.drivers import DriversController


URLS = (
    '/1/drivers', DriversController,
    '/1/drivers/(.+)/edit', EditDriverController,
) + (() if not web.config.DEV else (
    # Develop routes
))
