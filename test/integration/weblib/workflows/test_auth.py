#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock

from app.weblib.workflows.auth import LoginFacebookWorkflow
from app.weblib.workflows.auth import LoginFakeWorkflow
from app.weblib.adapters.auth import AlwaysFailOAuthAdapter
from app.weblib.adapters.auth import AlwaysSuccessOAuthAdapter


class TestLoginFakeWorkflow(unittest.TestCase):

    def test_cannot_proceed_if_already_authorized(self):
        # Given
        logger = Mock()
        subscriber = Mock(already_authorized=MagicMock())
        instance = LoginFakeWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {'fake_access_token': '123'}, None)

        # Then
        subscriber.already_authorized.assert_called_with()

    def test_authentication_completes_successfully(self):
        # Given
        logger = Mock()
        codegenerator = lambda: '1245'
        subscriber = Mock(oauth_success=MagicMock())
        instance = LoginFakeWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {}, codegenerator)

        # Then
        subscriber.oauth_success.assert_called_with(None, '1245')


class TestLoginFacebookWorkflow(unittest.TestCase):

    def test_cannot_proceed_if_already_authorized(self):
        # Given
        logger = Mock()
        subscriber = Mock(already_authorized=MagicMock())
        instance = LoginFacebookWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {'facebook_access_token': '123'}, None, None,
                         None, None, None)

        # Then
        subscriber.already_authorized.assert_called_with()

    def test_cannot_proceed_if_user_denies_permissions(self):
        # Given
        logger = Mock()
        subscriber = Mock(permission_denied=MagicMock())
        instance = LoginFacebookWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {}, Mock(code=None), None, None, None, None)

        # Then
        subscriber.permission_denied.assert_called_with()

    def test_authentication_code_is_required(self):
        # Given
        logger = Mock()
        subscriber = Mock(code_required=MagicMock())
        instance = LoginFacebookWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {}, Mock(error=None, code=None),
                         'redirect_here', 'application_id', None, None)

        # Then
        url = 'https://www.facebook.com/dialog/oauth?'
        url += 'scope='
        url += '&redirect_uri=redirect_here'
        url += '&response_type=code'
        url += '&client_id=application_id'
        subscriber.code_required.assert_called_with(url)


    def test_cannot_proceed_if_something_goes_wrong_while_reaching_oauth_server(self):
        # Given
        logger = Mock()
        oauthadapter = AlwaysFailOAuthAdapter()
        subscriber = Mock(oauth_error=MagicMock())
        instance = LoginFacebookWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {}, Mock(error=None, code='1245'),
                         'redirect_here', 'application_id',
                         'application_secret', oauthadapter)

        # Then
        url = 'https://graph.facebook.com/oauth/access_token?'
        url += 'client_secret=application_secret&'
        url += 'code=1245&'
        url += 'client_id=application_id&'
        url += 'redirect_uri=redirect_here'
        subscriber.oauth_error.assert_called_with(url, '501',
                                                  'Internal server error')

    def test_authentication_completes_successfully(self):
        # Given
        logger = Mock()
        oauthadapter = AlwaysSuccessOAuthAdapter()
        subscriber = Mock(oauth_success=MagicMock())
        instance = LoginFacebookWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, {}, Mock(error=None, code='1245'),
                         'redirect_here', 'application_id',
                         'application_secret', oauthadapter)

        # Then
        url = 'https://graph.facebook.com/oauth/access_token?'
        url += 'client_secret=application_secret&'
        url += 'code=1245&'
        url += 'client_id=application_id&'
        url += 'redirect_uri=redirect_here'
        subscriber.oauth_success.assert_called_with(url, {})
