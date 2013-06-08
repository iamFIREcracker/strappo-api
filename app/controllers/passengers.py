#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizableController
from app.repositories.passengers import PassengersRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.passengers import PassengersWorkflow


class PassengersController(ParamAuthorizableController):
    #@api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        drivers = PassengersWorkflow()
        ret = Future()

        class PassengersSubscriber(object):
            def not_found(self, driver_id):
                ret.set(jsonify(passengers=[]))
            def success(self, blob):
                ret.set(jsonify(passengers=blob))

        drivers.add_subscriber(logger, PassengersSubscriber())
        drivers.perform(web.ctx.logger, PassengersRepository)
        return ret.get()

