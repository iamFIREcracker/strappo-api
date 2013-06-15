#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Passenger
from app.models import User
from app.repositories.destinations import DestinationsRepository


class TestDestinationsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = Passenger.query

    def tearDown(self):
        self.session.remove()

    def test_get_all_without_passengers_should_return_empty_list(self):
        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_invalid_user_should_return_empty_list(self):
        # Given
        self.session.add(Passenger(id='pid', user_id='not_existing_id'))
        self.session.commit()
        self.session.remove()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_deleted_user_should_return_empty_list(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals([], destinations)

    def test_get_all_with_passenger_linked_to_active_user_should_return_the_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', destination='dest'))
        self.session.commit()
        self.session.remove()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals(1, len(destinations))
        self.assertEquals('dest', destinations[0][0])

    def test_get_predefined_should_return_hardcoded_values(self):
        # When
        destinations = DestinationsRepository.get_predefined()

        # Then
        self.assertEquals(5, len(destinations))
        self.assertEquals(('Darsena', 10), destinations[0])
        self.assertEquals(('Mojito Bar', 10), destinations[1])
        self.assertEquals(('Cosmopolitan', 10), destinations[2])
        self.assertEquals(('Red Lion', 10), destinations[3])
        self.assertEquals(('Club Negroni', 10), destinations[4])

    def test_most_used_destinations_come_first(self):
        # Given
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
        self.session.remove()

        # When
        destinations = DestinationsRepository.get_all()

        # Then
        self.assertEquals(2, len(destinations))
        self.assertEquals('dest2', destinations[0][0])
        self.assertEquals('dest1', destinations[1][0])
