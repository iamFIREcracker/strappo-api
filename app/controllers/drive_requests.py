#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizableController
from app.repositories.drive_requests import DriveRequestsRepository
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
            def success(self, blob):
                ret.set(jsonify(drive_requests=blob))

        accepted_requests.add_subscriber(logger,
                                         ListActiveDriveRequestsSubscriber())
        accepted_requests.perform(web.ctx.logger, DriveRequestsRepository,
                                  web.input(driver_id=None, passenger_id=None))
        return ret.get()
