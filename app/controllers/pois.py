#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.workflows.pois import ListActivePOISWorkflow


class ListActivePOISController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        list_pois = ListActivePOISWorkflow()
        ret = Future()

        class ListActivePOISSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self, blob):
                ret.set(jsonify(pois=blob))

        list_pois.add_subscriber(logger, ListActivePOISSubscriber())
        list_pois.perform(web.ctx.logger, web.config.APP_POIS)
        return ret.get()
