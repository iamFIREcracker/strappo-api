#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock
from web.utils import storage

from app.workflows.drive_requests import AcceptDriveRequestWorkflow
from app.workflows.drive_requests import AddDriveRequestWorkflow
from app.workflows.drive_requests import ListActiveDriveRequestsWorkflow


class TestListAcceptedPassengersWorkflow(unittest.TestCase):

    def test_success_message_with_no_drive_request_if_driver_id_is_invalid(self):
        # Given
        logger = Mock()
        repository = Mock(get_all_active_by_driver=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, storage(driver_id=None))

        # Then
        subscriber.success.assert_called_with([])

    def test_success_message_with_drive_requests_if_driver_id_is_valid(self):
        # Given
        logger = Mock()
        active_requests = [storage(id='rid1', accepted=True,
                                   driver=storage(id='did',
                                                  license_plate='plate',
                                                  telephone='phone',
                                                  hidden=False,
                                                  user=storage(name='name',
                                                               avatar='avatar',
                                                               id='uid')),
                                   passenger=storage(id='pid1',
                                                     origin='origin1',
                                                     destination='destination1',
                                                     seats=1,
                                                     user=storage(name='name1',
                                                                  avatar='avatar1',
                                                                  id='uid1'))),
                            storage(id='rid2', accepted=False,
                                   driver=storage(id='did',
                                                  license_plate='plate',
                                                  telephone='phone',
                                                  hidden=False,
                                                  user=storage(name='name',
                                                               avatar='avatar',
                                                               id='uid')),
                                    passenger=storage(id='pid2',
                                                      origin='origin2',
                                                      destination='destination2',
                                                      seats=2,
                                                      user=storage(name='name2',
                                                                   avatar='avatar2',
                                                                   id='uid2')))]
        repository = Mock(get_all_active_by_driver=MagicMock(return_value=active_requests))
        subscriber = Mock(success=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, storage(driver_id='did'))

        # Then
        subscriber.success.assert_called_with([{
            'id': 'rid1',
            'accepted': True,
            'driver': {
                'license_plate': 'plate',
                'hidden': False,
                'id': 'did',
                'telephone': 'phone',
                'user': {
                    'id': 'uid',
                    'name': 'name',
                    'avatar': 'avatar'
                }
            },
            'passenger': {
                'origin': 'origin1',
                'destination': 'destination1',
                'seats': 1,
                'id': 'pid1',
                'user': {
                    'id': 'uid1',
                    'name': 'name1',
                    'avatar': 'avatar1'
                }
            }
        }, {
            'id': 'rid2',
            'accepted': False,
            'driver': {
                'license_plate': 'plate',
                'hidden': False,
                'id': 'did',
                'telephone': 'phone',
                'user': {
                    'id': 'uid',
                    'name': 'name',
                    'avatar': 'avatar'
                }
            },
            'passenger': {
                'origin': 'origin2',
                'destination': 'destination2',
                'seats': 2,
                'id': 'pid2',
                'user': {
                    'id': 'uid2',
                    'name': 'name2',
                    'avatar': 'avatar2'
                }
            }
        }])


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

