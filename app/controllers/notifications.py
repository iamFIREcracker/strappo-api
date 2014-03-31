#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib
import urllib2
import uuid

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.traces import TracesRepository
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.workflows.notifications import ResetNotificationsWorkflow



class ResetNotificationsController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        data = web.input(data=None)
        logger = LoggingSubscriber(web.ctx.logger)
        reset_notifications = ResetNotificationsWorkflow()

        class ResetNotificationsSubscriber(object):
            def success(self):
                web.ctx.orm.commit()
                raise app.weblib.nocontent()

        reset_notifications.add_subscriber(logger,
                                           ResetNotificationsSubscriber())
        reset_notifications.perform(web.ctx.logger, web.ctx.redis,
                                    self.current_user.id)
