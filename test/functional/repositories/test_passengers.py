#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Passenger
from app.models import RideRequest
from app.models import User
from app.repositories.passengers import PassengersRepository


class TestPassengersRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = Passenger.query

    def tearDown(self):
        self.session.remove()

    def test_get_with_invalid_id_should_return_nothing(self):
        # When
        passenger = PassengersRepository.get('not_existing_id')

        # Then
        self.assertIsNone(passenger)

    def test_get_with_passenger_linked_to_invalid_user_should_return_nothing(self):
        # Given
        self.session.add(Passenger(id='pid', user_id='not_existing_id'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.get('pid')

        # Then
        self.assertIsNone(passenger)

    def test_get_with_passenger_linked_to_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.get('pid')

        # Then
        self.assertIsNone(passenger)

    def test_get_with_passenger_linked_to_active_user_should_return_the_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.get('pid')

        # Then
        self.assertIsNotNone(passenger)

    def test_get_all_active_without_passengers_should_return_empty_list(self):
        # When
        passengers = PassengersRepository.get_all_active()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_active_with_passenger_linked_to_invalid_user_should_return_empty_list(self):
        # Given
        self.session.add(Passenger(id='pid', user_id='not_existing_id'))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_active()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_active_with_passenger_linked_to_deleted_user_should_return_empty_list(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_active()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_active_with_deactivate_passenger_linked_to_deleted_user_should_return_empty_list(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', active=False))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_active()

        # Then
        self.assertEquals([], passengers)

    def test_get_all_active_with_passenger_linked_to_active_user_should_return_the_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_active()

        # Then
        self.assertEquals(1, len(passengers))
        self.assertEquals('pid', passengers[0].id)

    def test_get_all_accepted_by_driver_does_not_return_passengers_linked_to_deleted_users(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar', deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid', active=True))
        self.session.add(RideRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=True))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_accepted_by_driver('did')

        # Then
        self.assertEquals([], passengers)

    def test_get_all_accepted_by_driver_does_not_return_passengers_not_active(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', active=False))
        self.session.add(RideRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=True))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_accepted_by_driver('did')

        # Then
        self.assertEquals([], passengers)

    def test_get_all_accepted_by_driver_does_not_return_passengers_not_accepted(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', active=True))
        self.session.add(RideRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=False))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_accepted_by_driver('did')

        # Then
        self.assertEquals([], passengers)

    def test_get_all_accepted_by_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid', active=True))
        self.session.add(RideRequest(id='rrid', driver_id='did',
                                     passenger_id='pid', accepted=True))
        self.session.commit()
        self.session.remove()

        # When
        passengers = PassengersRepository.get_all_accepted_by_driver('did')

        # Then
        self.assertEquals(1, len(passengers))
        self.assertEquals('pid', passengers[0].id)

    def test_add_passenger_with_all_the_valid_fields_should_return_a_new_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.add('uid', 'origin', 'destination', 42)
        self.session.add(passenger)
        self.session.commit()
        passenger = self.query.filter_by(id=passenger.id).first()

        # Then
        self.assertEquals(42, passenger.seats)

    def test_deactivate_passenger_with_invalid_id_should_return_nothing(self):
        # When
        passenger = PassengersRepository.deactivate('pid')

        # Then
        self.assertIsNone(passenger)

    def test_deactivate_passenger_linked_to_invalid_user_id_should_return_nothing(self):
        # Given
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.deactivate('pid')

        # Then
        self.assertIsNone(passenger)

    def test_deactivate_passenger_linked_to_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        passenger = PassengersRepository.deactivate('pid')

        # Then
        self.assertIsNone(passenger)

    def test_deactivate_passenger_linked_to_active_user_should_return_deactivated_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Passenger(id='pid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        self.session.add(PassengersRepository.deactivate('pid'))
        self.session.commit()
        passenger = self.query.filter_by(id='pid').first()

        # Then
        self.assertEquals(False, passenger.active)
