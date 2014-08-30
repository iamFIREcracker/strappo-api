#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import groupby

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.traces import TracesRepository
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.request_decorators import internal
from app.workflows.traces import AddTracesWorkflow
from app.workflows.traces import ListTracesWorkflow
from app.weblib.pubsub import Future
from app.weblib.utils import jsonify

class ListTracesController():
    @internal([web.config.ANALYTICS_IP])
    def GET(self):
        data = web.input(limit=1000, offset=0)
        logger = LoggingSubscriber(web.ctx.logger)
        traces = ListTracesWorkflow()
        ret = Future()

        class ListTracesSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(traces=blob))


        traces.add_subscriber(logger, ListTracesSubscriber())
        traces.perform(web.ctx.logger, TracesRepository,
                       data.limit, data.offset)
        return ret.get()


class AddTracesController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        data = web.input(data=None)
        logger = LoggingSubscriber(web.ctx.logger)
        add_traces = AddTracesWorkflow()

        class AddTracesSubscriber(object):
            def success(self):
                web.ctx.orm.commit()
                raise app.weblib.nocontent()

        add_traces.add_subscriber(logger, AddTracesSubscriber())
        add_traces.perform(web.ctx.orm, web.ctx.logger, self.current_user.id,
                           TracesRepository, data.data)
