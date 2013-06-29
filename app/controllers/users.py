#!/usr/bin/env python
# -*- coding: utf-8 -*-


import web

from app.controllers import ParamAuthorizableController
from app.repositories.users import UsersRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.workflows.users import ViewUserWorkflow
from app.weblib.utils import jsonify



class ViewUserController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        view_user = ViewUserWorkflow()
        ret = Future()

        class ViewUserSubscriber(object):
            def not_found(self, user_id):
                raise web.notfound()
            def success(self, blob):
                ret.set(jsonify(user=blob))

        view_user.add_subscriber(logger, ViewUserSubscriber())
        view_user.perform(web.ctx.logger, UsersRepository, passenger_id)
        return ret.get()
