#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizableController
from app.repositories.drivers import DriversRepository
from app.repositories.drive_requests import DriveRequestsRepository
from app.repositories.passengers import PassengersRepository
from app.repositories.rates import RatesRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.drive_requests import ListActiveDriveRequestsWorkflow


class ListActiveDriveRequestsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        accepted_requests = ListActiveDriveRequestsWorkflow()
        ret = Future()

        class ListActiveDriveRequestsSubscriber(object):
            def bad_request(self):
                raise web.badrequest()
            def unauthorized(self):
                raise web.unauthorized()
            def success(self, blob):
                ret.set(jsonify(drive_requests=blob))

        accepted_requests.add_subscriber(logger,
                                         ListActiveDriveRequestsSubscriber())
        accepted_requests.perform(web.ctx.logger, DriversRepository,
                                  PassengersRepository,
                                  DriveRequestsRepository, RatesRepository,
                                  self.current_user.id, web.input())
        return ret.get()
