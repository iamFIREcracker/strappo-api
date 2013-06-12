#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import Passenger
from app.models import User
from app.repositories.destinations import DestinationsRepository


class TestDestinationsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        cls.session = Passenger.session
        cls.query = Passenger.query

    def setUp(self):
        Passenger.session.begin(subtransactions=True)

    def tearDown(self):
        Passenger.session.rollback()
        Passenger.session.remove()

    def test_get_all_without_passengers_should_return_empty_list(self):
        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_invalid_user_should_return_empty_list(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Passenger(id='pid', user_id='not_existing_id'))
        self.session.commit()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_deleted_user_should_return_empty_list(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_active_user_should_return_the_passenger(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', destination='dest'))
        self.session.commit()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals(1, len(destinations))
        self.assertEquals('dest', destinations[0][0])

    def test_most_used_destinations_come_first(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid1', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid1', user_id='uid1',
                                   destination='dest1'))
        self.session.add(User(id='uid2', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid2', user_id='uid2',
                                   destination='dest2'))
        self.session.add(User(id='uid3', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid3', user_id='uid3',
                                   destination='dest2'))
        self.session.commit()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals(2, len(destinations))
        self.assertEquals('dest2', destinations[0][0])
        self.assertEquals('dest1', destinations[1][0])
