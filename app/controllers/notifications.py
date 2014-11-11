#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib
import urllib2

import web
import weblib
from strappon.repositories.traces import TracesRepository
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized

from app.controllers import ParamAuthorizableController
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
                raise weblib.nocontent()

        reset_notifications.add_subscriber(logger,
                                           ResetNotificationsSubscriber())
        reset_notifications.perform(web.ctx.logger, web.ctx.redis,
                                    self.current_user.id)
