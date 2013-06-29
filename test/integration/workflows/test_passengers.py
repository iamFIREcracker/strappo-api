#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import ActivePassengersWorkflow
from app.workflows.passengers import ViewPassengerWorkflow
from app.workflows.passengers import NotifyPassengerWorkflow


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
                              destination='destination1', seats=1,
                              user=storage(name='Name1', avatar='Avatar1',
                                           id='uid1')),
                      storage(id='pid2', user_id='uid2', origin='origin2',
                              destination='destination2', seats=2,
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
        instance.perform(orm, logger, params, None, None, None)

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
        instance.perform(orm, logger, params, repository, 'uid',
                         drivers_notifier)

        # Then
        subscriber.success.assert_called_with('pid')


class TestViewPassengerWorkflow(unittest.TestCase):
    def test_with_invalid_id_should_publish_a_not_found(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing')

        # Then
        subscriber.not_found.assert_called_with('not_existing')

    def test_with_existing_id_should_return_serialized_passenger(self):
        # Given
        logger = Mock()
        passenger = storage(id='pid', user_id='uid', origin='origin',
                            destination='destination', seats=1,
                            user=storage(id='uid', name='name',
                                         avatar='avatar'))
        repository = Mock(get=MagicMock(return_value=passenger))
        subscriber = Mock(success=MagicMock())
        instance = ViewPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid')

        # Then
        subscriber.success.assert_called_with({
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

    def test_failure_message_is_published_if_something_goes_wrong_with_the_push_adapter(self):
        # Given
        logger = Mock()
        passenger = storage(user=storage(device=storage(device_token='dt1')))
        repository = Mock(get=MagicMock(return_value=passenger))
        push_adapter = Mock(notify_tokens=MagicMock(return_value=(None,
                                                                  'Error!')))
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
        passenger = storage(user=storage(device=storage(device_token='dt1')))
        repository = Mock(get=MagicMock(return_value=passenger))
        push_adapter = Mock(notify_tokens=MagicMock(return_value=(None, None)))
        subscriber = Mock(success=MagicMock())
        instance = NotifyPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'pid', push_adapter, None, None)

        # Then
        subscriber.success.assert_called_with()
