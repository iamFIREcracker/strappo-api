#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import ActivePassengersWorkflow
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
                              destination='destination1', buddies=1,
                              user=storage(name='Name1', avatar='Avatar1')),
                      storage(id='pid2', user_id='uid2', origin='origin2',
                              destination='destination2', buddies=2,
                              user=storage(name='Name2', avatar='Avatar2'))]
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
            'name': 'Name1',
            'buddies': 1,
            'id': 'pid1',
            'avatar': 'Avatar1'
        }, {
            'origin': 'origin2',
            'destination': 'destination2',
            'name': 'Name2',
            'buddies': 2,
            'id': 'pid2',
            'avatar': 'Avatar2'
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
        instance.perform(orm, logger, params, None, None)

        # Then
        subscriber.invalid_form.assert_called_with({
            'destination': 'Required',
            'buddies': 'Required'
        })

    def test_successfully_create_a_passenger_when_all_the_fields_are_valid(self):
        # Given
        orm = Mock()
        logger = Mock()
        params = storage(origin='heaven', destination='hell', buddies=4)
        passenger = storage(id='pid', user_id='uid', origin='heaven',
                            destination='hell', buddies=4)
        repository = Mock(add=MagicMock(return_value=passenger))
        subscriber = Mock(success=MagicMock())
        instance = AddPassengerWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, params, repository, 'uid')

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
                            destination='destination', buddies=1,
                            user=storage(name='name', avatar='avatar'))
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
            'name': 'name',
            'buddies': 1,
            'id': 'pid',
            'avatar': 'avatar'
        })
