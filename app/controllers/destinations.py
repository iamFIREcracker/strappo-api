#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.controllers import ParamAuthorizableController
from app.repositories.destinations import DestinationsRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.destinations import ListDestinationsWorkflow


class ListDestinationsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        list_destinations = ListDestinationsWorkflow()
        ret = Future()

        class ListDestinationsSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(destinations=blob))

        list_destinations.add_subscriber(logger, ListDestinationsSubscriber())
        list_destinations.perform(web.ctx.logger,
                                  DestinationsRepository.get_all)
        return ret.get()


class ListPredefinedDestinationsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        list_destinations = ListDestinationsWorkflow()
        ret = Future()

        class ListDestinationsSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(destinations=blob))

        list_destinations.add_subscriber(logger, ListDestinationsSubscriber())
        list_destinations.perform(web.ctx.logger,
                                  DestinationsRepository.get_predefined)
        return ret.get()

