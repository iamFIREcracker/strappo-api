#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
from datetime import datetime

import web

from app.weblib.workflows.auth import LoginFacebookWorkflow
from app.weblib.workflows.auth import FakeLoginWorkflow
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub.auth import CodeExtractor
from app.weblib.pubsub.auth import InSessionVerifier
from app.weblib.pubsub.auth import OAuthInvoker


class FakeLoginController(object):
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        loginfake = FakeLoginWorkflow()

        class FakeLoginSubscriber(object):
            def already_authorized(self):
                raise web.found(web.ctx.path_url + '/authorized')
            def oauth_success(self, url, content):
                web.ctx.session['fake_access_token'] = content
                raise web.found(web.ctx.path_url + '/authorized')

        codegenerator = hashlib.sha256(str(datetime.now())).digest
        loginfake.add_subscriber(logger, FakeLoginSubscriber())
        loginfake.perform(web.ctx.logger, web.ctx.session, codegenerator)


class LoginFacebookController():
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        loginfacebook = LoginFacebookWorkflow()

        class LoginFacebookSubscriber(object):
            def already_authorized(self):
                raise web.found(web.ctx.path_url + '/authorized')
            def permission_denied(self):
                # XXX flash some message here!
                raise web.found('/')
            def generate_code(self, url):
                raise web.found(url)
            def oauth_error(self, url, status, content):
                # XXX flash some message here
                raise web.found('/')
            def oauth_success(self, url, content):
                web.ctx.session['facebook_access_token'] = content
                raise web.found(web.ctx.path_url + '/authorized')

        loginfacebook.add_subscriber(logger, LoginFacebookSubscriber())
        loginfacebook.perform(web.ctx.logger, 
                              InSessionVerifier(), CodeExtractor(),
                              OAuthInvoker(), web.ctx.path_url,
                              web.ctx.session, web.input(error=None, code=None),
                              web.config.FACEBOOK_APP_ID,
                              web.config.FACEBOOK_APP_SECRET)
