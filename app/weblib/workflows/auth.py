#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urlparse

from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub.auth import CodeExtractor
from app.weblib.pubsub.auth import InSessionVerifier
from app.weblib.pubsub.auth import OAuthInvoker


class FakeLoginWorkflow(Publisher):
    """Defines a workflow managing a fake OAuth authentication."""

    def perform(self, logger, session, codegenerator):
        """Performs the necessary steps to obtain a fake access token."""
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        sessionverifier = InSessionVerifier()

        class InSessionVerifierSubscriber(object):
            def session_contains(self, key, value):
                outer.publish('already_authorized')
            def session_lacks(self, key):
                token = codegenerator()
                outer.publish('oauth_success', None, token)

        sessionverifier.add_subscriber(logger, InSessionVerifierSubscriber())
        sessionverifier.perform(session, 'fake_access_token')


class LoginFacebookWorkflow(Publisher):
    """Defines a workflow managing the authentication with Facebook."""

    AUTHORIZE_URL = 'https://www.facebook.com/dialog/oauth'
    ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'

    def perform(self, logger, session, params, redirect_uri, app_id, app_secret,
                oauthadapter):
        """Performs the necessary steps to obtain a Facebook access token.

        This publisher is able to emits a lot of messages, namely:
        - 'already_authorized' in case an access toke has already been
          added to the request session;
        - 'permission_denied' in case the client denied permissions to our
          application;
        - 'code_required' in case no authentication code has been found in the
          request parameters list, together by the URI to contact to request
          the aforementioned code;
        - 'oauth_error' in case something went wrong while doing the final oauth
          authentication request, together with the request URL, status code and
          content;
        - 'oauth_success' if everything went fine, together with the access
          token;
        """
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        sessionverifier = InSessionVerifier()
        oauthinvoker = OAuthInvoker()
        codeextractor = CodeExtractor()

        class InSessionVerifierSubscriber(object):
            def session_contains(self, key, value):
                outer.publish('already_authorized')
            def session_lacks(self, key):
                codeextractor.perform(params)

        class CodeExtractorSubscriber(object):
            def permission_denied(self):
                outer.publish('permission_denied')
            def code_absent(self):
                qs = dict(client_id=app_id, redirect_uri=redirect_uri,
                        response_type='code', scope='')
                outer.publish('code_required',
                              outer.AUTHORIZE_URL + '?' + urllib.urlencode(qs))
            def code_valid(self, code):
                client = oauthadapter.create_client(app_id, app_secret)
                qs = dict(code=code, client_id=app_id, client_secret=app_secret,
                        redirect_uri=redirect_uri)
                url = outer.ACCESS_TOKEN_URL + '?' + urllib.urlencode(qs)
                oauthinvoker.perform(client, url)

        class OAuthInvokerSubscriber(object):
            def oauth_error(self, url, status, content):
                outer.publish('oauth_error', url, status, content)

            def oauth_success(self, url, content):
                outer.publish('oauth_success', url, urlparse.parse_qs(content))

        sessionverifier.add_subscriber(logger, InSessionVerifierSubscriber())
        codeextractor.add_subscriber(logger, CodeExtractorSubscriber())
        oauthinvoker.add_subscriber(logger, OAuthInvokerSubscriber())
        sessionverifier.perform(session, 'facebook_access_token')
