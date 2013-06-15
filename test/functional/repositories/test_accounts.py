#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        pass

    def tearDown(self):
        Account.session.rollback()

    @unittest.skip('For some reason this interfers with the next test...')
    def test_added_account_is_then_returned_inside_a_query(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        account = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.add(account)
        self.session.commit()
        account = self.query.filter_by(id=account.id).first()

        # Then
        self.assertEquals('facebook', account.type)

    def test_added_account_does_not_override_previously_created_ones(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                                 type='facebook'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        account = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.add(account)
        self.session.commit()
        account = self.query.filter_by(id=account.id).first()

        # Then
        self.assertNotEquals('aid', id)
        self.assertEquals('uid', account.user_id)
