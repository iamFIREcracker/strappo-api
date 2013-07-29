#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock
from web.utils import storage

from app.workflows.drive_requests import AcceptDriveRequestWorkflow
from app.workflows.drive_requests import AddDriveRequestWorkflow
from app.workflows.drive_requests import DeactivateActiveDriveRequestsWorkflow
from app.workflows.drive_requests import ListActiveDriveRequestsWorkflow


class TestListAcceptedPassengersWorkflow(unittest.TestCase):

    def test_unauthorized_message_is_published_on_invalid_driver_id(self):
        # Given
        logger = Mock()
        drivers_repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, drivers_repository, None, None, None,
                         storage(driver_id=None))

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_different_registered_user_cannot_fetch_drive_requests_of_different_drivers(self):
        # Given
        logger = Mock()
        drivers_repository = Mock(get=MagicMock(return_value=Mock()))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, drivers_repository, None, None, 'uid',
                         storage(driver_id=None))

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_success_message_with_drive_requests_if_driver_id_is_valid(self):
        # Given
        logger = Mock()
        drivers_repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        active_requests = [storage(id='rid1', accepted=True,
                                   driver=storage(id='did',
                                                  license_plate='plate',
                                                  telephone='phone',
                                                  hidden=False,
                                                  user=storage(name='name',
                                                               avatar='avatar',
                                                               id='uid')),
                                   passenger=storage(id='pid1',
                                                     matched=False,
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
                                                      matched=True,
                                                      origin='origin2',
                                                      destination='destination2',
                                                      seats=2,
                                                      user=storage(name='name2',
                                                                   avatar='avatar2',
                                                                   id='uid2')))]
        requests_repository = Mock(get_all_active_by_driver=MagicMock(return_value=active_requests))
        subscriber = Mock(success=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, drivers_repository, None, requests_repository,
                         'uid', storage(driver_id='did'))

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
                'matched': False,
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
                'matched': True,
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

    def test_unauthorized_message_is_published_on_invalid_passenger_id(self):
        # Given
        logger = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, None, passengers_repository, None, None,
                         storage(passenger_id=None))

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_different_registered_user_cannot_fetch_drive_requests_of_different_passengers(self):
        # Given
        logger = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=Mock()))
        subscriber = Mock(unauthorized=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, None, passengers_repository, None, 'uid',
                         storage(passenger_id=None))

        # Then
        subscriber.unauthorized.assert_called_with()

    def test_success_message_with_drive_requests_if_passenger_id_is_valid(self):
        # Given
        logger = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        active_requests = [storage(id='rid1', accepted=True,
                                   driver=storage(id='did1',
                                                  license_plate='plate1',
                                                  telephone='phone1',
                                                  hidden=False,
                                                  user=storage(name='name1',
                                                               avatar='avatar1',
                                                               id='uid1')),
                                   passenger=storage(id='pid',
                                                     matched=False,
                                                     origin='origin',
                                                     destination='destination',
                                                     seats=1,
                                                     user=storage(name='name',
                                                                  avatar='avatar',
                                                                  id='uid'))),
                            storage(id='rid2', accepted=False,
                                   driver=storage(id='did2',
                                                  license_plate='plate2',
                                                  telephone='phone2',
                                                  hidden=False,
                                                  user=storage(id='uid2',
                                                               name='name2',
                                                               avatar='avatar2')),
                                    passenger=storage(id='pid',
                                                      matched=True,
                                                      origin='origin',
                                                      destination='destination',
                                                      seats=2,
                                                      user=storage(id='uid',
                                                                   name='name',
                                                                   avatar='avatar')))]
        requests_repository = Mock(get_all_active_by_passenger=MagicMock(return_value=active_requests))
        subscriber = Mock(success=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, None, passengers_repository,
                         requests_repository, 'uid',
                         storage(passenger_id='pid'))

        # Then
        subscriber.success.assert_called_with([{
            'id': 'rid1',
            'accepted': True,
            'driver': {
                'license_plate': 'plate1',
                'hidden': False,
                'id': 'did1',
                'telephone': 'phone1',
                'user': {
                    'id': 'uid1',
                    'name': 'name1',
                    'avatar': 'avatar1'
                }
            },
            'passenger': {
                'matched': False,
                'origin': 'origin',
                'destination': 'destination',
                'seats': 1,
                'id': 'pid',
                'user': {
                    'id': 'uid',
                    'name': 'name',
                    'avatar': 'avatar'
                }
            }
        }, {
            'id': 'rid2',
            'accepted': False,
            'driver': {
                'id': 'did2',
                'license_plate': 'plate2',
                'telephone': 'phone2',
                'hidden': False,
                'user': {
                    'id': 'uid2',
                    'name': 'name2',
                    'avatar': 'avatar2'
                }
            },
            'passenger': {
                'id': 'pid',
                'matched': True,
                'origin': 'origin',
                'destination': 'destination',
                'seats': 2,
                'user': {
                    'id': 'uid',
                    'name': 'name',
                    'avatar': 'avatar'
                }
            }
        }])

    def test_bad_request_is_generated_if_neither_driver_and_passenger_id_is_set(self):
        # Given
        logger = Mock()
        subscriber = Mock(bad_request=MagicMock())
        instance = ListActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, None, None, None, None, storage())

        # Then
        subscriber.bad_request.assert_called_with()


class TestAddDriveRequestWorkflow(unittest.TestCase):

    def test_drive_request_cannot_be_created_for_not_existing_driver(self):
        # Given
        logger = Mock()
        orm = Mock()
        drivers_repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AddDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drivers_repository, 'uid',
                         'not_existing_id', None, None, None)

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_drive_request_cannot_be_created_by_another_registered_user(self):
        # Given
        logger = Mock()
        orm = Mock()
        drivers_repository = Mock(get=MagicMock())
        subscriber = Mock(unauthorized=MagicMock())
        instance = AddDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drivers_repository, 'uid', 'did', None,
                         None, None)

        # Then
        subscriber.unauthorized.assert_called_with()


    def test_drive_request_is_successfully_created_when_workflow_is_executed(self):
        # Given
        logger = Mock()
        orm = Mock()
        drivers_repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        requests_repository = Mock(add=MagicMock())
        task = Mock()
        subscriber = Mock(success=MagicMock())
        instance = AddDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, drivers_repository, 'uid', 'did',
                         requests_repository, 'pid', task)

        # Then
        subscriber.success.assert_called_with()


class TestAcceptDriveRequestWorkflow(unittest.TestCase):
    def test_drive_request_for_not_existing_passenger_cannot_be_accepted(self):
        # Given
        logger = Mock()
        orm = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, passengers_repository, 'not_existing_id',
                         None, None, None)

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')


    def test_drive_request_cannot_be_accepted_by_another_registered_user(self):
        # Given
        logger = Mock()
        orm = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=Mock()))
        subscriber = Mock(unauthorized=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, passengers_repository, 'pid', 'uid',
                         None, None)

        # Then
        subscriber.unauthorized.assert_called_with()


    def test_not_found_is_published_if_no_drive_requests_exists_associated_with_given_ids(self):
        # Given
        logger = Mock()
        orm = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        drive_requests_repository = Mock(accept=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, passengers_repository, 'pid', 'uid',
                         drive_requests_repository, 'invalid_pid')

        # Then
        subscriber.not_found.assert_called_with()

    def test_success_is_published_if_passenger_associated_with_request_is_invalid(self):
        # Given
        logger = Mock()
        orm = Mock()
        passengers_repository = Mock(get=MagicMock(return_value=Mock(user_id='uid')))
        request = storage(id='rid', driver_id='did', passenger_id='pid',
                          passenger=storage())
        drive_requests_repository = Mock(accept=MagicMock(return_value=request))
        subscriber = Mock(success=MagicMock())
        instance = AcceptDriveRequestWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(orm, logger, passengers_repository, 'pid', 'uid',
                         drive_requests_repository, 'did')

        # Then
        subscriber.success.assert_called_with()


class TestDeactivateActiveDriveRequestsWorkflow(unittest.TestCase):
    def test_no_drive_request_is_deactivated_if_no_drive_request_is_active(self):
        # Given
        logger = Mock()
        orm = Mock()
        repository = Mock(get_all_active=MagicMock(return_value=[]))
        subscriber = Mock(success=MagicMock())
        instance = DeactivateActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([])

    def test_active_drive_requests_get_properly_hidden(self):
        logger = Mock()
        orm = Mock()
        drive_requests = [storage(id='r1', active=True),
                          storage(id='r2', active=True)]
        repository = Mock(get_all_active=MagicMock(return_value=drive_requests))
        subscriber = Mock(success=MagicMock())
        instance = DeactivateActiveDriveRequestsWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, orm, repository)

        # Then
        subscriber.success.assert_called_with([
            storage(id='r1', active=False),
            storage(id='r2', active=False)
        ])
