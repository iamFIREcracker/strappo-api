#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers.auth import FakeLoginAuthorizedController
from app.controllers.destinations import ListDestinationsController
from app.controllers.destinations import ListPredefinedDestinationsController
from app.controllers.drivers import AcceptPassengerController
from app.controllers.drivers import EditDriverController
from app.controllers.drivers import DriversController
from app.controllers.drivers import HideDriverController
from app.controllers.drivers import UnhideDriverController
from app.controllers.passengers import AddPassengerController
from app.controllers.passengers import AcceptDriverController
from app.controllers.passengers import ActivePassengersController
from app.controllers.passengers import ViewPassengerController
from app.weblib.controllers.auth import FakeLoginController


URLS = (
    '/1/destinations', ListDestinationsController,
    '/1/destinations/predefined', ListPredefinedDestinationsController,
    '/1/drivers', DriversController,
    '/1/drivers/(.+)/edit', EditDriverController,
    '/1/drivers/(.+)/hide', HideDriverController,
    '/1/drivers/(.+)/unhide', UnhideDriverController,
    '/1/drivers/(.+)/accept/passenger/(.+)', AcceptPassengerController,
    '/1/passengers/active', ActivePassengersController,
    '/1/passengers/add', AddPassengerController,
    '/1/passengers/(.+)/view', ViewPassengerController,
    '/1/passengers/(.+)/accept/driver/(.+)', AcceptDriverController,
) + (() if not web.config.DEV else (
    # Develop routes
    '/login/fake', FakeLoginController,
    '/login/fake/authorized', FakeLoginAuthorizedController
))
