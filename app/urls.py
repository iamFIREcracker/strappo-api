#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.controllers.destinations import ListDestinationsController
from app.controllers.destinations import ListPredefinedDestinationsController
from app.controllers.drivers import AcceptPassengerController
from app.controllers.drivers import AddDriverController
from app.controllers.drivers import EditDriverController
from app.controllers.drivers import HideDriverController
from app.controllers.drivers import UnhideDriverController
from app.controllers.drivers import ViewDriverController
from app.controllers.drive_requests import ListActiveDriveRequestsController
from app.controllers.passengers import AddPassengerController
from app.controllers.passengers import AcceptDriverController
from app.controllers.passengers import ActivePassengersController
from app.controllers.passengers import ViewPassengerController
from app.controllers.users import LoginUserController
from app.controllers.users import ViewUserController


URLS = (
    '/1/destinations', ListDestinationsController,
    '/1/destinations/predefined', ListPredefinedDestinationsController,
    '/1/drivers/add', AddDriverController,
    '/1/drivers/(.+)/view', ViewDriverController,
    '/1/drivers/(.+)/edit', EditDriverController,
    '/1/drivers/(.+)/hide', HideDriverController,
    '/1/drivers/(.+)/unhide', UnhideDriverController,
    '/1/drivers/(.+)/accept/passenger/(.+)', AcceptPassengerController,
    '/1/drive_requests/active', ListActiveDriveRequestsController,
    '/1/passengers/active', ActivePassengersController,
    '/1/passengers/add', AddPassengerController,
    '/1/passengers/(.+)/view', ViewPassengerController,
    '/1/passengers/(.+)/accept/driver/(.+)', AcceptDriverController,
    '/1/users/(.+)/view', ViewUserController,
    '/1/users/login', LoginUserController
)
