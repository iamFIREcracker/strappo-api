#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import DriveRequest
from app.repositories.drive_requests import DriveRequestsRepository


class TestDriveRequestsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = DriveRequest.query

    def tearDown(self):
        self.session.remove()

    def test_add_drive_request_with_all_the_valid_fields_should_return_a_new_drive_request(self):
        # When
        request = DriveRequestsRepository.add('did', 'pid')
        self.session.add(request)
        self.session.commit()
        request = self.query.filter_by(id=request.id).first()

        # Then
        self.assertEquals('did', request.driver_id)
        self.assertEquals('pid', request.passenger_id)
        self.assertEquals(False, request.accepted)

    def test_cannot_accept_a_drive_request_passing_wrong_driver_id(self):
        # Given
        self.session.add(DriveRequest(id='rrid', driver_id='did',
                                     passenger_id='pid'))
        self.session.commit()
        self.session.remove()

        # When
        request = DriveRequestsRepository.accept('invalid_id', 'pid')

        # Then
        self.assertIsNone(request)

    def test_cannot_accept_a_drive_request_passing_wrong_passenger_id(self):
        # Given
        self.session.add(DriveRequest(id='rrid', driver_id='did',
                                     passenger_id='pid'))
        self.session.commit()
        self.session.remove()

        # When
        request = DriveRequestsRepository.accept('did', 'invalid_id')

        # Then
        self.assertIsNone(request)

    def test_cannot_accept_a_drive_request_already_accepted(self):
        # Given
        self.session.add(DriveRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=True))
        self.session.commit()
        self.session.remove()

        # When
        request = DriveRequestsRepository.accept('did', 'pid')

        # Then
        self.assertIsNone(request)

    def test_cannot_accept_an_inactive_drive_request(self):
        # Given
        self.session.add(DriveRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=False,
                                     active=False))
        self.session.commit()
        self.session.remove()

        # When
        request = DriveRequestsRepository.accept('did', 'pid')

        # Then
        self.assertIsNone(request)

    def test_accept_a_drive_request_should_set_the_accepted_property(self):
        # Given
        self.session.add(DriveRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=False,
                                     active=True))
        self.session.commit()
        self.session.remove()

        # When
        self.session.add(DriveRequestsRepository.accept('did', 'pid'))
        self.session.commit()
        request = self.query.filter_by(id='rrid').first()

        # Then
        self.assertEquals(True, request.accepted)