#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Driver
from app.models import Passenger
from app.models import Token
from app.models import User
from app.repositories.users import UsersRepository


class TestUsersRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = User.query

    def tearDown(self):
        self.session.remove()

    def test_get_with_invalid_id_should_return_nothing(self):
        # When
        user = UsersRepository.get('not_existing_id')

        # Then
        self.assertIsNone(user)

    def test_get_with_id_of_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNone(user)

    def test_get_with_id_of_active_user_should_return_it(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNotNone(user)
        self.assertIsNone(user.driver)
        self.assertIsNone(user.passenger)

    def test_get_with_active_user_should_return_the_user_and_the_linked_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNotNone(user)
        self.assertEqual('did', user.driver.id)

    def test_get_with_active_user_should_return_the_user_and_not_the_linked_inactive_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Passenger(id='pid', user_id='uid', active=False))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNotNone(user)
        self.assertIsNone(user.passenger)

    def test_get_with_active_user_should_return_the_user_and_the_linked_active_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Passenger(id='pid', user_id='uid', active=True))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNotNone(user)
        self.assertEqual('pid', user.passenger.id)

    def test_get_with_active_user_should_return_the_user_and_only_the_linked_active_passenger(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Passenger(id='pid1', user_id='uid', active=False))
        self.session.add(Passenger(id='pid2', user_id='uid', active=True))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.get('uid')

        # Then
        self.assertIsNotNone(user)
        self.assertEqual('pid2', user.passenger.id)

    def test_added_user_is_then_returned_inside_a_query(self):
        # When
        user = UsersRepository.add('ACSID', 'Name', 'Avatar')
        self.session.add(user)
        self.session.commit()
        user = self.query.filter_by(id=user.id).first()

        # Then
        self.assertEquals('Avatar', user.avatar)

    def test_authorized_by_invalid_token_should_return_nothing(self):
        # When
        user = UsersRepository.authorized_by('not_existing')

        # Then
        self.assertIsNone(user)

    def test_authorized_by_valid_token_pointing_to_invalid_user_should_return_nothing(self):
        # Given
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.authorized_by('tid')

        # Then
        self.assertIsNone(user)

    def test_authorized_by_valid_token_pointing_to_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.authorized_by('tid')

        # Then
        self.assertIsNone(user)

    def test_authorized_by_valid_token_should_return_the_associated_user(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.authorized_by('tid')

        # Then
        self.assertEquals('uid', user.id)

    def test_having_acs_id_with_invalid_external_id_should_return_nothing(self):
        # When
        user = UsersRepository.with_acs_id('not_existing')

        # Then
        self.assertIsNone(user)

    def test_having_acs_id_pointing_to_a_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', acs_id='acid', name='Name',
                              avatar='Avatar', deleted=True))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.with_acs_id('acid')

        # Then
        self.assertIsNone(user)

    def test_having_acs_id_with_valid_id_should_return_the_associated_user(self):
        # Given
        self.session.add(User(id='uid', acs_id='acid', name='Name',
                              avatar='Avatar'))
        self.session.commit()
        self.session.remove()

        # When
        user = UsersRepository.with_acs_id('acid')

        # Then
        self.assertEquals('uid', user.id)
