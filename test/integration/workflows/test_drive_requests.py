#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock
from web.utils import storage

from app.workflows.drive_requests import AcceptDriveRequestWorkflow
from app.workflows.drive_requests import AddDriveRequestWorkflow


class TestAddDriveRequestWorkflow(unittest.TestCase):

    def test_drive_request_is_successfully_created_when_workflow_is_executed(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(add=MagicMock())
        task = Mock()
        subscriber = Mock(success=MagicMock())
        instance = AddDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, repository, 'did', 'pid', task)

        # Then
        subscriber.success.assert_called_with()


class TestAcceptDriveRequestWorkflow(unittest.TestCase):

    def test_not_found_is_published_if_no_drive_requests_exists_associated_with_given_ids(self):
        # Given
        logger = Mock()
        orm = Mock()
        drive_requests_repository = Mock(accept=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drive_requests_repository, 'invalid_did',
                         'invalid_pid', None)

        # Then
        subscriber.not_found.assert_called_with()

    def test_not_found_is_published_if_passenger_associated_with_request_was_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        request = storage(id='rid', driver_id='did', passenger_id='pid')
        drive_requests_repository = Mock(accept=MagicMock(return_value=request))
        passengers_repository = Mock(deactivate=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drive_requests_repository, 'did', 'pid',
                         passengers_repository)

        # Then
        subscriber.not_found.assert_called_with()

    def test_success_is_published_if_passenger_associated_with_request_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        request = storage(id='rid', driver_id='did', passenger_id='pid')
        drive_requests_repository = Mock(accept=MagicMock(return_value=request))
        passengers_repository = Mock(deactivate=MagicMock())
        subscriber = Mock(success=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drive_requests_repository, 'did', 'pid',
                         passengers_repository)

        # Then
        subscriber.success.assert_called_with()

