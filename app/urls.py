#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.controllers import InfoController
from app.controllers.drive_requests import ListActiveDriveRequestsController
from app.controllers.drive_requests import ListUnratedDriveRequestsController
from app.controllers.drivers import AcceptPassengerController
from app.controllers.drivers import AddDriverController
from app.controllers.drivers import CancelDriveOfferController
from app.controllers.drivers import DeactivateDriverController
from app.controllers.drivers import RateDriveRequestController
from app.controllers.feedbacks import AddFeedbackController
from app.controllers.notifications import ResetNotificationsController
from app.controllers.passengers import AcceptDriverController
from app.controllers.passengers import CalculateFareController
from app.controllers.passengers import AddPassengerController
from app.controllers.passengers import AlightPassengerController
from app.controllers.passengers import CancelDriveRequestController
from app.controllers.passengers import DeactivatePassengerController
from app.controllers.passengers import ListUnmatchedPassengersController
from app.controllers.traces import AddTracesController
from app.controllers.users import ActivatePromoController
from app.controllers.users import LoginUserController
from app.controllers.users import ViewUserController


URLS = (
    '/1/info', InfoController,

    '/1/users/login', LoginUserController,
    '/1/users/(.+)/view', ViewUserController,
    '/1/users/(.+)/activate_promo', ActivatePromoController,

    '/1/drivers/add', AddDriverController,
    '/1/drivers/(.+)/deactivate', DeactivateDriverController,
    '/1/drivers/(.+)/accept/passenger/(.+)', AcceptPassengerController,
    '/1/drivers/(.+)/cancel/drive_request/(.+)', CancelDriveOfferController,
    '/1/drivers/(.+)/rate/drive_request/(.+)', RateDriveRequestController,

    '/1/passengers/unmatched', ListUnmatchedPassengersController,
    '/1/passengers/calculate_fare', CalculateFareController,
    '/1/passengers/add', AddPassengerController,
    '/1/passengers/(.+)/deactivate', DeactivatePassengerController,
    '/1/passengers/(.+)/alight', AlightPassengerController,
    '/1/passengers/(.+)/accept/driver/(.+)', AcceptDriverController,
    '/1/passengers/(.+)/cancel/drive_request/(.+)',
    CancelDriveRequestController,

    '/1/drive_requests/active', ListActiveDriveRequestsController,
    '/1/drive_requests/unrated', ListUnratedDriveRequestsController,

    '/1/traces/add', AddTracesController,

    '/1/feedbacks/add', AddFeedbackController,

    '/1/notifications/reset', ResetNotificationsController,
)
