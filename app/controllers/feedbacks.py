#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import weblib
from strappon.repositories.feedbacks import FeedbacksRepository
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.workflows.feedbacks import AddFeedbackWorkflow


class AddFeedbackController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        logger = LoggingSubscriber(web.ctx.logger)
        add_feedback = AddFeedbackWorkflow()
        ret = Future()

        class AddFeedbackSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))

            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        add_feedback.add_subscriber(logger, AddFeedbackSubscriber())
        add_feedback.perform(web.ctx.gettext, web.ctx.orm, web.ctx.logger,
                             FeedbacksRepository, self.current_user,
                             web.input())
        return ret.get()
