#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import Passenger
from app.models import User
from app.repositories.passengers import PassengersRepository


class TestPassengersRepository(unittest.TestCase):
    
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
        passengers = PassengersRepository.get_all()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_with_passenger_linked_to_invalid_user_should_return_empty_list(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Passenger(id='pid', user_id='not_existing_id'))
        self.session.commit()

        # When
        passengers = PassengersRepository.get_all()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_with_passenger_linked_to_deleted_user_should_return_empty_list(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()

        # When
        passengers = PassengersRepository.get_all()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_with_passenger_linked_to_active_user_should_return_the_passenger(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()

        # When
        passengers = PassengersRepository.get_all()

        # Then
        self.assertEquals(1, len(passengers))
        self.assertEquals('pid', passengers[0].id)
