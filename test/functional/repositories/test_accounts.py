#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import unittest

from app.models import Account
from app.models import User
from app.repositories.users import AccountsRepository


class TestAccountsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        cls.session = Account.session
        cls.query = Account.query

    def setUp(self):
        Account.session.begin(subtransactions=True)

    def tearDown(self):
        Account.session.rollback()
        Account.session.remove()

    def test_added_account_is_then_returned_inside_a_query(self):
        # When
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', phone='Phone',
                              avatar='Avatar'))
        id = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.commit()
        account = self.query.filter_by(id=id).first()

        # Then
        self.assertEquals('facebook', account.type)

    def test_get_not_existing_account_should_return_nothing(self):
        # When
        account = AccountsRepository.get('uid', 'eid', 'facebook')

        # Then
        self.assertIsNone(account)

    def test_get_existing_account_with_wrong_account_type_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()

        # When
        account = AccountsRepository.get('uid', 'eid', 'twitter')

        # Then
        self.assertIsNone(account)

    def test_get_existing_account_with_proper_parameters_but_deleted_account_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()

        # When
        account = AccountsRepository.get('uid', 'eid', 'facebook')

        # Then
        self.assertIsNone(account)

    def test_get_existing_account_with_proper_parameters_should_return_the_account(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', phone='Phone',
                              avatar='Avatar'))
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                         type='facebook'))
        self.session.commit()

        # When
        account = AccountsRepository.get('uid', 'eid', 'facebook')

        # Then
        self.assertEquals('aid', account.id)

    def test_get_existing_account_should_return_the_latest_account_record(self):
        # Given
        now = datetime.datetime.now()
        now_plus_1day = now + datetime.timedelta(days=1)
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', phone='Phone',
                              avatar='Avatar'))
        self.session.add(Account(id='aid1', user_id='uid', external_id='eid',
                         type='facebook', created=now))
        self.session.add(Account(id='aid2', user_id='uid', external_id='eid',
                         type='facebook', created=now_plus_1day))
        self.session.commit()

        # When
        account = AccountsRepository.get('uid', 'eid', 'facebook')

        # Then
        self.assertEquals('aid2', account.id)
