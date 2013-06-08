#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import web
from web.utils import storage

from app.controllers import CookieAuthorizedController
from app.repositories.users import UsersRepository
from app.workflows.users import LoginAuthorizedWorkflow
from app.weblib.pubsub import LoggingSubscriber


class FakeLoginAuthorizedController(CookieAuthorizedController):
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        login_authorized = LoginAuthorizedWorkflow()

        def paramsextractor(token):
            return storage(externalid=unicode(uuid.uuid4()), name='John Smith',
                           phone='+123 345346',
                           avatar='http://www.placehold.it/128x128/EFEFEF/AAAAAA&text=no+image')

        class LoginAuthorizedSubscriber(object):
            def not_authorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                web.ctx.session.pop('fake_access_token')
                raise web.internalerror()
            def success(self, token):
                web.ctx.orm.commit()
                web.ctx.session.pop('fake_access_token')
                web.setcookie('token', token.id) # XXX expiration date
                raise web.found('/profile')

        login_authorized.add_subscriber(logger, LoginAuthorizedSubscriber())
        login_authorized.perform(web.ctx.orm, web.ctx.logger, web.ctx.session,
                                 'fake_access_token', paramsextractor,
                                 UsersRepository, 'fake')
