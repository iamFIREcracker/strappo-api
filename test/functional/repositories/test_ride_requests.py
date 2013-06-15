#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import RideRequest
from app.repositories.ride_requests import RideRequestsRepository


class TestRideRequestsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        cls.session = RideRequest.session
        cls.query = RideRequest.query

    def setUp(self):
        pass

    def tearDown(self):
        RideRequest.session.rollback()
        RideRequest.session.remove()

    def test_add_ride_request_with_all_the_valid_fields_should_return_a_new_ride_request(self):
        # When
        self.session.begin(subtransactions=True)
        ride_request = RideRequestsRepository.add('did', 'pid')
        self.session.add(ride_request)
        self.session.commit()
        ride_request = self.query.filter_by(id=ride_request.id).first()

        # Then
        self.assertEquals('did', ride_request.driver_id)
        self.assertEquals('pid', ride_request.passenger_id)
        self.assertEquals(False, ride_request.accepted)
