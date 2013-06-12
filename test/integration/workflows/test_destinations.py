#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock

from app.workflows.destinations import ListDestinationsWorkflow


class TestListDestinationsWorkflow(unittest.TestCase):
    def test_get_all_destinations_without_any_registered_passenger_should_return_an_empty_list(self):
        # Given
        logger = Mock()
        repository = Mock(get_all=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = ListDestinationsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_get_all_passengers_should_return_serialized_passengers(self):
        # Given
        logger = Mock()
        destinations = [('dest1', 10), ('dest2', 5), ('dest3', 1)]
        repository = Mock(get_all=MagicMock(return_value=destinations))
        subscriber = Mock(success=MagicMock())
        instance = ListDestinationsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository)

        # Then
        subscriber.success.assert_called_with([
            'dest1',
            'dest2',
            'dest3'
        ])
