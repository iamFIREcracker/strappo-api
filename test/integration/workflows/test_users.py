#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.users import LoginAuthorizedWorkflow


class TestLoginAuthorizedWorkflow(unittest.TestCase):
    
    def test_cannot_proceed_if_not_authorized(self):
        # Given
        logger = Mock()
        orm = Mock()
        subscriber = Mock(not_authorized=MagicMock())
        instance = LoginAuthorizedWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, {}, 'access_token', None, None, None)

        # Then
        subscriber.not_authorized.assert_called_with()

    def test_unregistered_user_cannot_proceed_with_one_or_more_fields_missing(self):
        # Given
        logger = Mock()
        orm = Mock()
        paramsextractor = MagicMock(return_value=storage(externalid='eid'))
        repository = Mock(with_account=MagicMock(return_value=None))
        subscriber = Mock(invalid_form=MagicMock())
        instance = LoginAuthorizedWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, {'access_token': 1234}, 'access_token',
                         paramsextractor, repository, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'errors': {
                'name': 'Required',
                'avatar': 'Should be a valid URL.'
            },
            'success': False
        })

    def test_unregistered_user_gets_registered_and_a_token_is_assigned(self):
        # Given
        logger = Mock()
        orm = Mock()
        paramsextractor = MagicMock(return_value=storage(externalid='eid',
                                                         name='Name',
                                                         avatar='http://...'))
        repository = Mock(with_account=MagicMock(return_value=None),
                          refresh_account=MagicMock(return_value='account'),
                          refresh_token=MagicMock(return_value='token'))
        subscriber = Mock(success=MagicMock())
        instance = LoginAuthorizedWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, {'access_token': 1234}, 'access_token',
                         paramsextractor, repository, None)

        # Then
        subscriber.success.assert_called_with('token')

    def test_registered_user_can_refresh_authentication_token(self):
        # Given
        logger = Mock()
        orm = Mock()
        paramsextractor = MagicMock(return_value=storage(externalid='eid'))
        repository = Mock(with_account=MagicMock(),
                          refresh_account=MagicMock(return_value='account'),
                          refresh_token=MagicMock(return_value='token'))
        subscriber = Mock(success=MagicMock())
        instance = LoginAuthorizedWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, {'access_token': 1234}, 'access_token',
                         paramsextractor, repository, None)

        # Then
        subscriber.success.assert_called_with('token')
