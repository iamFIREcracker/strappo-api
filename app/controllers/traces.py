#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.traces import TracesRepository
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.workflows.traces import AddTracesWorkflow


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
