#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.drivers import AddDriverWorkflow
from app.workflows.drivers import HideDriverWorkflow
from app.workflows.drivers import DriversWithUserIdWorkflow
from app.workflows.drivers import EditDriverWorkflow
from app.workflows.drivers import ListAcceptedPassengersWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import UnhideDriverWorkflow
from app.workflows.drivers import ViewDriverWorkflow


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
                         telephone='+124 453534', hidden=False,
                         user=storage(name='name', avatar='avatar'))
        repository = Mock(with_user_id=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = DriversWithUserIdWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did')

        # Then
        subscriber.success.assert_called_with({
            'hidden': False,
            'id': 'did',
            'license_plate': '1242124',
            'telephone': '+124 453534',
        })


class TestViewDriverWorkflow(unittest.TestCase):
    
    def test_not_found_is_published_if_invoked_with_invalid_driver_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_serialized_driver_is_published_if_invoked_with_an_existing_driver_id(self):
        # Given
        logger = Mock()
        driver = storage(id='did', user_id='uid', license_plate='1242124',
                         telephone='+124 453534', hidden=False,
                         user=storage(name='name', avatar='avatar'))
        repository = Mock(get=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id')

        # Then
        subscriber.success.assert_called_with({
            'hidden': False,
            'id': 'did',
            'license_plate': '1242124',
            'telephone': '+124 453534',
        })


class TestAddDriverWorkflow(unittest.TestCase):
    def test_cannot_add_a_new_driver_without_specifying_required_fields(self):
        # Given
        orm = Mock()
        logger = Mock()
        params = storage(license_plate='plate')
        subscriber = Mock(invalid_form=MagicMock())
        instance = AddDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, None, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'telephone': 'Required'
        })

    def test_successfully_create_a_driver_when_all_the_fields_are_valid(self):
        # Given
        orm = Mock()
        logger = Mock()
        params = storage(license_plate='plate', telephone='phone')
        driver = storage(id='pid', user_id='uid', license_plate='plate',
                         telephone='phone')
        repository = Mock(add=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = AddDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'uid')

        # Then
        subscriber.success.assert_called_with('pid')




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


class TestListAcceptedPassengersWorkflow(unittest.TestCase):

    def test_success_message_with_no_passengers_if_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        repository = Mock(get_all_accepted_by_driver=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = ListAcceptedPassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'invalid_id')

        # Then
        subscriber.success.assert_called_with([])

    def test_success_message_with_accepted_passengers_if_driver_id_is_valid(self):
        # Given
        logger = Mock()
        active_passengers = [storage(id='pid1', origin='origin1',
                                     destination='destination1', seats=1,
                                     user=storage(name='name1',
                                                  avatar='avatar1')),
                             storage(id='pid2', origin='origin2',
                                     destination='destination2', seats=2,
                                     user=storage(name='name2',
                                                  avatar='avatar2'))]
        repository = Mock(get_all_accepted_by_driver=MagicMock(return_value=active_passengers))
        subscriber = Mock(success=MagicMock())
        instance = ListAcceptedPassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did')

        # Then
        subscriber.success.assert_called_with([{
            'origin': 'origin1',
            'destination': 'destination1',
            'name': 'name1',
            'seats': 1,
            'id': 'pid1',
            'avatar': 'avatar1'
        }, {
            'origin': 'origin2',
            'destination': 'destination2',
            'name': 'name2',
            'seats': 2,
            'id': 'pid2',
            'avatar': 'avatar2'
        }])


class TestNotifyDriversWorkflow(unittest.TestCase):
    def test_failure_message_is_published_if_something_goes_wrong_with_the_push_adapter(self):
        # Given
        logger = Mock()
        drivers = [storage(user=storage(device=storage(device_token='dt1'))),
                   storage(user=storage(device=storage(device_token='dt2')))]
        repository = Mock(get_all_unhidden=MagicMock(return_value=drivers))
        push_adapter = Mock(notify_tokens=MagicMock(return_value=(None,
                                                                  'Error!')))
        subscriber = Mock(failure=MagicMock())
        instance = NotifyDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, push_adapter, None, None)

        # Then
        subscriber.failure.assert_called_with('Error!')

    def test_success_message_is_published_if_the_push_adapters_accomplishes_its_duties(self):
        # Given
        logger = Mock()
        drivers = [storage(user=storage(device=storage(device_token='dt1'))),
                   storage(user=storage(device=storage(device_token='dt2')))]
        repository = Mock(get_all_unhidden=MagicMock(return_value=drivers))
        push_adapter = Mock(notify_tokens=MagicMock(return_value=(None, None)))
        subscriber = Mock(success=MagicMock())
        instance = NotifyDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, push_adapter, None, None)

        # Then
        subscriber.success.assert_called_with()
