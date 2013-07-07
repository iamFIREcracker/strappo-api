#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.users import LoginUserWorkflow
from app.workflows.users import ViewUserWorkflow


class TestViewUserWorkflow(unittest.TestCase):
    def test_with_invalid_id_should_publish_a_not_found(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing')

        # Then
        subscriber.not_found.assert_called_with('not_existing')

    def test_with_existing_id_should_return_serialized_user(self):
        # Given
        logger = Mock()
        user = storage(id='uid', name='name', avatar='avatar',
                       passenger=storage(id='pid', origin='origin',
                                         destination='destination', seats=1),
                       driver=None)
        repository = Mock(get=MagicMock(return_value=user))
        subscriber = Mock(success=MagicMock())
        instance = ViewUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'uid')

        # Then
        subscriber.success.assert_called_with({
            'id': 'uid',
            'name': 'name',
            'avatar': 'avatar',
            'driver': None,
            'passenger': {
                'id': 'pid',
                'origin': 'origin',
                'destination': 'destination',
                'seats': 1,
            }
        })


class TestLoginUserWorkflow(unittest.TestCase):

    def test_unregistered_user_cannot_proceed_with_invalid_facebook_token(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(with_acs_id=MagicMock(return_value=None))
        adapter = Mock(profile=MagicMock(return_value=(None, 'error')))
        subscriber = Mock(internal_error=MagicMock())
        instance = LoginUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'acs_id', adapter, 'invalid')

        # Then
        subscriber.internal_error.assert_called_with()

    def test_unregistered_user_cannot_proceed_with_one_or_more_fields_missing(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(with_acs_id=MagicMock(return_value=None))
        adapter = Mock(profile=MagicMock(return_value=(storage(id='id',
                                                               name='Name'),
                                                       None)),
                       avatar=MagicMock(return_value=None))
        subscriber = Mock(invalid_form=MagicMock())
        instance = LoginUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'acs_id', adapter, 'valid')

        # Then
        subscriber.invalid_form.assert_called_with({
            'errors': {
                'avatar': 'Should be a valid URL.'
            },
            'success': False
        })

    def test_unregistered_user_gets_registered_and_a_token_is_assigned(self):
        # Given
        logger = Mock()
        orm = Mock()
        token = storage(id='tid', user_id='uid')
        repository = Mock(with_acs_id=MagicMock(return_value=None),
                          refresh_token=MagicMock(return_value=token))
        adapter = Mock(profile=MagicMock(return_value=(storage(id='id',
                                                               name='Name'),
                                                       None)),
                       avatar=MagicMock(return_value='http://...'))
        subscriber = Mock(success=MagicMock())
        instance = LoginUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'acs_id', adapter, 'valid')

        # Then
        subscriber.success.assert_called_with({
            'id': 'tid',
            'user_id': 'uid'
        })

    def test_registered_user_can_refresh_authentication_token(self):
        # Given
        logger = Mock()
        orm = Mock()
        token = storage(id='tid', user_id='uid')
        repository = Mock(with_acs_id=MagicMock(),
                          refresh_token=MagicMock(return_value=token))
        subscriber = Mock(success=MagicMock())
        instance = LoginUserWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'acs_id', None, None)

        # Then
        subscriber.success.assert_called_with({
            'id': 'tid',
            'user_id': 'uid'
        })
