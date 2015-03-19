#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.workflows.poi import ListActivePOIWorkflow


class ListActivePOIController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        list_poi = ListActivePOIWorkflow()
        ret = Future()

        class ListActivePOISubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self, blob):
                ret.set(jsonify(poi=blob))

        list_poi.add_subscriber(logger, ListActivePOISubscriber())
        list_poi.perform(web.ctx.logger, web.config.APP_POI)
        return ret.get()
