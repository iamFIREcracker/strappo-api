#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock
from web.utils import storage

from app.workflows.ride_requests import AcceptRideRequestWorkflow
from app.workflows.ride_requests import AddRideRequestWorkflow


class TestAddRideRequestWorkflow(unittest.TestCase):

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


class TestAcceptRideRequestWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_no_ride_requests_exists_associated_with_given_ids(self):
        # Given
        logger = Mock()
        orm = Mock()
        ride_requests_repository = Mock(accept=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptRideRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, ride_requests_repository, 'invalid_did',
                         'invalid_pid', None)

        # Then
        subscriber.not_found.assert_called_with()

    def test_not_found_is_published_if_passenger_associated_with_request_was_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        request = storage(id='rid', driver_id='did', passenger_id='pid')
        ride_requests_repository = Mock(accept=MagicMock(return_value=request))
        passengers_repository = Mock(deactivate=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptRideRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, ride_requests_repository, 'did', 'pid',
                         passengers_repository)

        # Then
        subscriber.not_found.assert_called_with()

    def test_success_is_published_if_passenger_associated_with_request_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        request = storage(id='rid', driver_id='did', passenger_id='pid')
        ride_requests_repository = Mock(accept=MagicMock(return_value=request))
        passengers_repository = Mock(deactivate=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = AcceptRideRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, ride_requests_repository, 'did', 'pid',
                         passengers_repository)

        # Then
        subscriber.success.assert_called_with()

