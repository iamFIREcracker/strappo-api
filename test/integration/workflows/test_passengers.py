#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import ActivePassengersWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow
from app.workflows.passengers import DeactivateActivePassengersWorkflow
from app.workflows.passengers import NotifyPassengerWorkflow
from app.workflows.passengers import ViewPassengerWorkflow


class TestActivePassengersWorkflow(unittest.TestCase):
    def test_get_all_active_passengers_without_any_registered_one_should_return_an_empty_list(self):
        # Given
        logger = Mock()
        repository = Mock(get_all_active=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = ActivePassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_get_all_active_passengers_should_return_serialized_passengers(self):
        # Given
        logger = Mock()
        passengers = [storage(id='pid1', user_id='uid1', origin='origin1',
                              destination='destination1', seats=1, matched=True,
                              user=storage(name='Name1', avatar='Avatar1',
                                           id='uid1')),
                      storage(id='pid2', user_id='uid2', origin='origin2',
                              destination='destination2', seats=2,
                              matched=False,
                              user=storage(name='Name2', avatar='Avatar2',
                                           id='uid2'))]
        repository = Mock(get_all_active=MagicMock(return_value=passengers))
        subscriber = Mock(success=MagicMock())
        instance = ActivePassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([{
            'matched': True,
            'origin': 'origin1',
            'destination': 'destination1',
            'seats': 1,
            'id': 'pid1',
            'user': {
                'id': 'uid1',
                'name': 'Name1',
                'avatar': 'Avatar1'
            }
        }, {
            'matched': False,
            'origin': 'origin2',
            'destination': 'destination2',
            'seats': 2,
            'id': 'pid2',
            'user': {
                'id': 'uid2',
                'name': 'Name2',
                'avatar': 'Avatar2'
            }
        }])


class TestAddPassengerWorkflow(unittest.TestCase):
    def test_cannot_add_a_new_passenger_without_specifying_required_fields(self):
        # Given
        orm = Mock()
        logger = Mock()
        params = storage(origin='heaven')
        subscriber = Mock(invalid_form=MagicMock())
        instance = AddPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, None, None, None, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'destination': 'Required',
            'seats': 'Required'
        })

    def test_successfully_create_a_passenger_when_all_the_fields_are_valid(self):
        # Given
        orm = Mock()
        logger = Mock()
        params = storage(origin='heaven', destination='hell', seats=4)
        passenger = storage(id='pid', user_id='uid', origin='heaven',
                            destination='hell', seats=4)
        repository = Mock(add=MagicMock(return_value=passenger))
        drivers_notifier = Mock()
        subscriber = Mock(success=MagicMock())
        instance = AddPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'uid', 'Name',
                         drivers_notifier)

        # Then
        subscriber.success.assert_called_with('pid')


class TestViewPassengerWorkflow(unittest.TestCase):
    def test_not_found_is_published_if_invoked_with_invalid_passenger_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing', None)

        # Then
        subscriber.not_found.assert_called_with('not_existing')

    def test_another_registered_user_not_having_drive_request_in_common_cannot_view_passenger(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=Mock(drive_requests=[])))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_serialized_passenger_is_published_if_invoked_by_passenger_owner(self):
        # Given
        logger = Mock()
        passenger = storage(id='pid', user_id='uid', origin='origin',
                            destination='destination', seats=1, matched=True,
                            user=storage(id='uid', name='name',
                                         avatar='avatar'))
        repository = Mock(get=MagicMock(return_value=passenger))
        subscriber = Mock(success=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', 'uid')

        # Then
        subscriber.success.assert_called_with({
            'matched': True,
            'origin': 'origin',
            'destination': 'destination',
            'seats': 1,
            'id': 'pid',
            'user': {
                'id': 'uid',
                'name': 'name',
                'avatar': 'avatar'
            }
        })

    def test_serialized_passenger_is_published_if_invoked_by_linked_driver(self):
        # Given
        logger = Mock()
        passenger = storage(id='pid', user_id='uid', origin='origin',
                            destination='destination', seats=1, matched=True,
                            user=storage(id='uid', name='name',
                                         avatar='avatar'),
                            drive_requests=[storage(driver=storage(id='did',
                                                                   user_id='uid2'))])
        repository = Mock(get=MagicMock(return_value=passenger))
        subscriber = Mock(success=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', 'uid2')

        # Then
        subscriber.success.assert_called_with({
            'matched': True,
            'origin': 'origin',
            'destination': 'destination',
            'seats': 1,
            'id': 'pid',
            'user': {
                'id': 'uid',
                'name': 'name',
                'avatar': 'avatar'
            }
        })


class TestNotifyPassengerWorkflow(unittest.TestCase):
    def test_cannot_notify_passenger_providing_an_invalid_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(passenger_not_found=MagicMock())
        instance = NotifyPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'invalid_id', None, None, None)

        # Then
        subscriber.passenger_not_found.assert_called_with('invalid_id')

    def test_failure_message_is_published_if_unable_to_log_into_acs(self):
        # Given
        logger = Mock()
        passenger = storage(user=storage(acs_id='acsid1'))
        repository = Mock(get=MagicMock(return_value=passenger))
        push_adapter = Mock(login=MagicMock(return_value=(None, 'Error!')))
        subscriber = Mock(failure=MagicMock())
        instance = NotifyPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', push_adapter, None, None)

        # Then
        subscriber.failure.assert_called_with('Error!')

    def test_failure_message_is_published_if_something_goes_wrong_with_the_push_adapter(self):
        # Given
        logger = Mock()
        passenger = storage(user=storage(acs_id='acsid1'))
        repository = Mock(get=MagicMock(return_value=passenger))
        push_adapter = Mock(login=MagicMock(return_value=('session', None)),
                            notify=MagicMock(return_value=(None, 'Error!')))
        subscriber = Mock(failure=MagicMock())
        instance = NotifyPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', push_adapter, None, None)

        # Then
        subscriber.failure.assert_called_with('Error!')

    def test_success_message_is_published_if_the_push_adapters_accomplishes_its_duties(self):
        # Given
        logger = Mock()
        passenger = storage(user=storage(acs_id='acsid1'))
        repository = Mock(get=MagicMock(return_value=passenger))
        push_adapter = Mock(login=MagicMock(return_value=('session', None)),
                            notify=MagicMock(return_value=(None, None)))
        subscriber = Mock(success=MagicMock())
        instance = NotifyPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', push_adapter, None, None)

        # Then
        subscriber.success.assert_called_with()


class TestDeactivatePassengerWorkflow(unittest.TestCase):
    def test_not_found_is_published_if_invoked_with_invalid_passenger_id(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = DeactivatePassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository, 'not_existing', None)

        # Then
        subscriber.not_found.assert_called_with('not_existing')

    def test_another_registered_user_not_having_drive_request_in_common_cannot_view_passenger(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get=MagicMock(return_value=Mock(drive_requests=[])))
        subscriber = Mock(unauthorized=MagicMock())
        instance = DeactivatePassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository, 'pid', 'uid')

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_passenger_gets_properly_deactivated_if_invoked_by_passenger_owner(self):
        # Given
        logger = Mock()
        orm = Mock()
        passenger = storage(id='pid', user_id='uid')
        repository = Mock(get=MagicMock(return_value=passenger))
        subscriber = Mock(success=MagicMock())
        instance = DeactivatePassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository, 'pid', 'uid')

        # Then
        subscriber.success.assert_called_with()


class TestDeactivateActivePassengersWorkflow(unittest.TestCase):
    def test_no_passenger_is_deactivated_if_no_passenger_is_active(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get_all_active=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = DeactivateActivePassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_active_passengers_get_properly_hidden(self):
        # Given
        logger = Mock()
        orm = Mock()
        passengers = [storage(id='p1', active=True),
                      storage(id='p2', active=True)]
        repository = Mock(get_all_active=MagicMock(return_value=passengers))
        subscriber = Mock(success=MagicMock())
        instance = DeactivateActivePassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([
            storage(id='p1', active=False),
            storage(id='p2', active=False)
        ])
