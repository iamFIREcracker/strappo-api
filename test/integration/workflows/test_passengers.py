#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.passengers import PassengersWorkflow


class TestPassengersWorkflow(unittest.TestCase):
    
    def test_get_all_passengers_without_any_registered_one_should_return_an_empty_list(self):
        # Given
        logger = Mock()
        repository = Mock(get_all=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = PassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_get_all_passengers_should_return_serialized_passengers(self):
        # Given
        logger = Mock()
        passengers = [storage(id='pid1', user_id='uid1', origin='origin1',
                              destination='destination1', buddies=1),
                      storage(id='pid2', user_id='uid2', origin='origin2',
                              destination='destination2', buddies=2)]
        repository = Mock(get_all=MagicMock(return_value=passengers))
        subscriber = Mock(success=MagicMock())
        instance = PassengersWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([{
            'origin': 'origin1',
            'destination': 'destination1',
            'user_id': 'uid1',
            'buddies': 1,
            'id': 'pid1'
        }, {
            'origin': 'origin2',
            'destination': 'destination2',
            'user_id': 'uid2',
            'buddies': 2,
            'id': 'pid2'
        }])
