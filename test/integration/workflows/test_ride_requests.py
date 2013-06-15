#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock

from app.workflows.ride_requests import AddRideRequestWorkflow


class TestAcceptPassengerWorkflow(unittest.TestCase):

    def test_ride_request_is_successfully_created_when_workflow_is_executed(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(add=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = AddRideRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'pid')

        # Then
        subscriber.success.assert_called_with()
