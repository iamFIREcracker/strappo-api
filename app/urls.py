#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers.auth import FakeLoginAuthorizedController
from app.controllers.drivers import EditDriverController
from app.controllers.drivers import DriversController
from app.weblib.controllers.auth import FakeLoginController


URLS = (
    '/1/drivers', DriversController,
    '/1/drivers/(.+)/edit', EditDriverController,
) + (() if not web.config.DEV else (
    # Develop routes
    '/login/fake', FakeLoginController,
    '/login/fake/authorized', FakeLoginAuthorizedController
))
