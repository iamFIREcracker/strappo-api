#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import weblib
from strappon.repositories.traces import TracesRepository
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized

from app.controllers import ParamAuthorizableController
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
                raise weblib.nocontent()

        add_traces.add_subscriber(logger, AddTracesSubscriber())
        add_traces.perform(web.ctx.orm, web.ctx.logger, self.current_user.id,
                           TracesRepository, data.data)
