#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import Account
from app.models import Token
from app.models import User
from app.repositories.users import UsersRepository


class TestUsersRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        # Misc
        cls.session = User.session

    def setUp(self):
        self.session.begin(subtransactions=True)

    def tearDown(self):
        self.session.rollback()
        self.session.remove()

    def test_authorized_by_invalid_token_should_return_nothing(self):
        # When
        user = UsersRepository.authorized_by('not_existing')

        # Then
        self.assertIsNone(user)

    def test_authorized_by_valid_token_pointing_to_invalid_user_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()

        # When
        user = UsersRepository.authorized_by('tid')

        # Then
        self.assertIsNone(user)

    def test_authorized_by_valid_token_should_return_the_associated_user(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', phone='Phone',
                         avatar='Avatar'))
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()

        # When
        user = UsersRepository.authorized_by('tid')

        # Then
        self.assertEquals('uid', user.id)

    def test_having_account_with_invalid_external_id_should_return_nothing(self):
        # When
        user = UsersRepository.with_account('not_existing', 'facebook')

        # Then
        self.assertIsNone(user)

    def test_having_account_with_invalid_account_type_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()
        # When
        user = UsersRepository.with_account('aid', 'twitter')

        # Then
        self.assertIsNone(user)

    def test_having_account_pointing_to_a_deleted_user_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()
        # When
        user = UsersRepository.with_account('aid', 'facebook')

        # Then
        self.assertIsNone(user)

    def test_having_account_with_valid_external_id_and_account_type_should_return_the_associated_user(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', phone='Phone',
                         avatar='Avatar'))
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()

        # When
        user = UsersRepository.with_account('eid', 'facebook')

        # Then
        self.assertEquals('uid', user.id)
