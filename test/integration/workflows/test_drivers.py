#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.drivers import HideDriverWorkflow
from app.workflows.drivers import DriversWithUserIdWorkflow
from app.workflows.drivers import EditDriverWorkflow
from app.workflows.drivers import UnhideDriverWorkflow


class TestDriversWithUserIdWorkflow(unittest.TestCase):
    
    def test_not_found_is_published_if_invoked_with_invalid_driver_id(self):
        # Given
        logger = Mock()
        repository = Mock(with_user_id=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = DriversWithUserIdWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_serialized_driver_is_published_if_invoked_with_existing_driver_id(self):
        # Given
        logger = Mock()
        driver = storage(id='did', user_id='uid', license_plate='1242124',
                         telephone='+124 453534', active=True,
                         user=storage(name='name', avatar='avatar'))
        repository = Mock(with_user_id=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = DriversWithUserIdWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did')

        # Then
        subscriber.success.assert_called_with({
            'user_id': 'uid',
            'name': 'name',
            'active': True,
            'id': 'did',
            'license_plate': '1242124',
            'avatar': 'avatar',
            'telephone': '+124 453534',
        })


class TestEditDriverWorkflow(unittest.TestCase):

    def test_invalid_form_is_published_if_the_list_of_params_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='plate')
        subscriber = Mock(invalid_form=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, None, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'telephone': 'Required'
        })

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='plate', telephone='Telephone')
        repository = Mock(update=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_is_successfully_updated_if_params_and_id_are_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='new_plate', telephone='new_phone')
        repository = Mock(update=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'did')

        # Then
        subscriber.success.assert_called_with()


class TestHideDriverWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(hide=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = HideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_is_successfully_hid_if_id_is_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(hide=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = HideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did')

        # Then
        subscriber.success.assert_called_with()


class TestUnhideDriverWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(unhide=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = UnhideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_is_successfully_unhid_if_id_is_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(unhide=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = UnhideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did')

        # Then
        subscriber.success.assert_called_with()
