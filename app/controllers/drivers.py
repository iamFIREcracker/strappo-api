#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizedController
from app.repositories.drivers import DriversRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.drivers import DriversWithUserIdWorkflow


class DriversController(ParamAuthorizedController):
    #@api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        drivers = DriversWithUserIdWorkflow()
        ret = Future()

        class DriversWithUserIdSubscriber(object):
            def not_found(self, driver_id):
                raise web.notfound()
            def driver_view(self, blob):
                ret.set(jsonify(blob))
        drivers.add_subscriber(logger, DriversWithUserIdSubscriber())
        drivers.perform(web.ctx.logger, DriversRepository,
                        web.input(user_id=None).user_id)
        return ret.get()
    
