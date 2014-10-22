#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizableController
from app.pubsub.drive_requests import ActiveDriveRequestsFilterExtractor
from app.repositories.drivers import DriversRepository
from app.repositories.drive_requests import DriveRequestsRepository
from app.repositories.passengers import PassengersRepository
from app.repositories.perks import PerksRepository
from app.repositories.rates import RatesRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.drive_requests import ListActiveDriverDriveRequestsWorkflow
from app.workflows.drive_requests import \
    ListActivePassengerDriveRequestsWorkflow
from app.workflows.drive_requests import ListUnratedDriveRequestsWorkflow


class ListActiveDriveRequestsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        filter_extractor = ActiveDriveRequestsFilterExtractor()
        list_driver_requests = ListActiveDriverDriveRequestsWorkflow()
        list_passenger_requests = ListActivePassengerDriveRequestsWorkflow()
        user_id = self.current_user.id
        params = web.input()
        ret = Future()

        class FilterExtractorSubscriber(object):
            def bad_request(self, params):
                raise web.badrequest()

            def by_driver_id_filter(self, driver_id):
                list_driver_requests.perform(web.ctx.logger,
                                             DriversRepository,
                                             DriveRequestsRepository,
                                             RatesRepository,
                                             PerksRepository,
                                             user_id,
                                             driver_id)

            def by_passenger_id_filter(self, passenger_id):
                list_passenger_requests.perform(web.ctx.logger,
                                                PassengersRepository,
                                                DriveRequestsRepository,
                                                RatesRepository,
                                                PerksRepository,
                                                user_id,
                                                passenger_id)

        class ListDriverDriveRequestsSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self, blob):
                ret.set(jsonify(drive_requests=blob))

        class ListPassengerDriveRequestsSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self, blob):
                ret.set(jsonify(drive_requests=blob))

        filter_extractor.add_subscriber(logger,
                                        FilterExtractorSubscriber())
        list_driver_requests.\
            add_subscriber(logger, ListDriverDriveRequestsSubscriber())
        list_passenger_requests.\
            add_subscriber(logger, ListPassengerDriveRequestsSubscriber())
        filter_extractor.perform(params)
        return ret.get()


class ListUnratedDriveRequestsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        accepted_requests = ListUnratedDriveRequestsWorkflow()
        ret = Future()

        class ListUnratedDriveRequestsSubscriber(object):
            def bad_request(self):
                raise web.badrequest()

            def unauthorized(self):
                raise web.unauthorized()

            def success(self, blob):
                ret.set(jsonify(drive_requests=blob))

        accepted_requests.add_subscriber(logger,
                                         ListUnratedDriveRequestsSubscriber())
        accepted_requests.perform(web.ctx.logger, DriversRepository,
                                  PassengersRepository,
                                  DriveRequestsRepository, RatesRepository,
                                  self.current_user.id, web.input())
        return ret.get()
