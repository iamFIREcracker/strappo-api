#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib
import urllib2
import uuid

import web
from web.utils import storage

from app.controllers import ParamAuthorizableController
from app.repositories.users import UsersRepository
from app.weblib.adapters.social.facebook import FacebookAdapter
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.workflows.users import LoginUserWorkflow
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


class LoginUserController(ParamAuthorizableController):
    @api
    def POST(self):
        data = web.input(acs_id=None, facebook_token=None)
        logger = LoggingSubscriber(web.ctx.logger)
        login_authorized = LoginUserWorkflow()
        ret = Future()

        class LoginAuthorizedSubscriber(object):
            def internal_error(self):
                web.ctx.orm.rollback()
                raise web.badrequest()
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                raise web.badrequest()
            def success(self, blob):
                web.ctx.orm.commit()
                ret.set(jsonify(token=blob))

        login_authorized.add_subscriber(logger, LoginAuthorizedSubscriber())
        login_authorized.perform(web.ctx.orm, web.ctx.logger, UsersRepository,
                                 data.acs_id, FacebookAdapter(),
                                 data.facebook_token)
        return ret.get()
