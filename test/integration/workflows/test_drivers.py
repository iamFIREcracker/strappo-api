#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.drivers import AddDriverWorkflow
from app.workflows.drivers import EditDriverWorkflow
from app.workflows.drivers import HideDriverWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import UnhideDriverWorkflow
from app.workflows.drivers import UnhideHiddenDriversWorkflow
from app.workflows.drivers import ViewDriverWorkflow


class TestViewDriverWorkflow(unittest.TestCase):
    
    def test_not_found_is_published_if_invoked_with_invalid_driver_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id', None)

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_another_registered_user_not_having_drive_request_in_common_cannot_view_driver(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=Mock(drive_requests=[])))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_serialized_driver_is_published_if_invoked_by_driver_owner(self):
        # Given
        logger = Mock()
        driver = storage(id='did', user_id='uid', license_plate='1242124',
                         telephone='+124 453534', hidden=False,
                         user=storage(name='name', avatar='avatar', id='uid'))
        repository = Mock(get=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did', 'uid')

        # Then
        subscriber.success.assert_called_with({
            'hidden': False,
            'id': 'did',
            'license_plate': '1242124',
            'telephone': '+124 453534',
            'user': {
                'id': 'uid',
                'name': 'name',
                'avatar': 'avatar',
            }
        })

    def test_serialized_driver_is_published_if_invoked_by_linked_passenger(self):
        # Given
        logger = Mock()
        driver = storage(id='did', user_id='uid', license_plate='1242124',
                         telephone='+124 453534', hidden=False,
                         user=storage(name='name', avatar='avatar', id='uid'),
                         drive_requests=[storage(passenger=storage(id='pid',
                                                                   user_id='uid2'))])
        repository = Mock(get=MagicMock(return_value=driver))
        subscriber = Mock(success=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'did', 'uid2')

        # Then
        subscriber.success.assert_called_with({
            'hidden': False,
            'id': 'did',
            'license_plate': '1242124',
            'telephone': '+124 453534',
            'user': {
                'id': 'uid',
                'name': 'name',
                'avatar': 'avatar',
            }
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
        instance.perform(orm, logger, params, None, None, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'telephone': 'Required'
        })

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='plate', telephone='Telephone')
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'not_existing_id', None)

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_cannot_be_update_from_another_registered_user(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='new_plate', telephone='new_phone')
        repository = Mock(get=MagicMock())
        subscriber = Mock(unauthorized=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'did', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()


    def test_driver_is_successfully_updated_if_params_and_id_are_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        params = storage(license_plate='new_plate', telephone='new_phone')
        repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        subscriber = Mock(success=MagicMock())
        instance = EditDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'did', 'uid')

        # Then
        subscriber.success.assert_called_with()


class TestHideDriverWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = HideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'not_existing_id', None)

        # THEN
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_cannot_be_hid_by_another_registered_user(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock())
        subscriber = Mock(unauthorized=MagicMock())
        instance = HideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_driver_is_successfully_hid_if_id_is_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        subscriber = Mock(success=MagicMock())
        instance = HideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'uid')

        # Then
        subscriber.success.assert_called_with()


class TestUnhideDriverWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_provided_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = UnhideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'not_existing_id', None)

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_driver_cannot_be_unhid_by_another_registered_user(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock())
        subscriber = Mock(unauthorized=MagicMock())
        instance = UnhideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()


    def test_driver_is_successfully_unhid_if_id_is_valid(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        subscriber = Mock(success=MagicMock())
        instance = UnhideDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'uid')

        # Then
        subscriber.success.assert_called_with()


class TestNotifyDriversWorkflow(unittest.TestCase):
    def test_failure_message_is_published_if_unable_to_log_into_acs(self):
        # Given
        logger = Mock()
        drivers = [storage(user=storage(acs_id='acsid1')),
                   storage(user=storage(acs_id='acsid2'))]
        repository = Mock(get_all_unhidden=MagicMock(return_value=drivers))
        push_adapter = Mock(login=MagicMock(return_value=(None, 'Error!')))
        subscriber = Mock(failure=MagicMock())
        instance = NotifyDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, push_adapter, None, None)

        # Then
        subscriber.failure.assert_called_with('Error!')


    def test_failure_message_is_published_if_something_goes_wrong_with_the_push_adapter(self):
        # Given
        logger = Mock()
        drivers = [storage(user=storage(acs_id='acsid1')),
                   storage(user=storage(acs_id='acsid2'))]
        repository = Mock(get_all_unhidden=MagicMock(return_value=drivers))
        push_adapter = Mock(login=MagicMock(return_value=('session_id', None)),
                            notify=MagicMock(return_value=(None, 'Error!')))
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
        drivers = [storage(user=storage(acs_id='acsid1')),
                   storage(user=storage(acs_id='acsid2'))]
        repository = Mock(get_all_unhidden=MagicMock(return_value=drivers))
        push_adapter = Mock(login=MagicMock(return_value=('session_id', None)),
                            notify=MagicMock(return_value=(None, None)))
        subscriber = Mock(success=MagicMock())
        instance = NotifyDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, push_adapter, None, None)

        # Then
        subscriber.success.assert_called_with()


class TestUnhideHiddenDriversWorkflow(unittest.TestCase):
    def test_no_driver_is_unhid_if_no_driver_is_hidden(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get_all_hidden=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = UnhideHiddenDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_hidden_drivers_get_properly_unhid(self):
        logger = Mock()
        orm = Mock()
        drivers = [storage(id='d1', hidden=True),
                   storage(id='d2', hidden=True)]
        repository = Mock(get_all_hidden=MagicMock(return_value=drivers))
        subscriber = Mock(success=MagicMock())
        instance = UnhideHiddenDriversWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([
            storage(id='d1', hidden=False),
            storage(id='d2', hidden=False)
        ])
