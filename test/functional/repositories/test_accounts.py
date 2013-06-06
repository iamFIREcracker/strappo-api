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
        Account.session.begin(subtransactions=True)

    def tearDown(self):
        Account.session.rollback()
        Account.session.remove()

    @unittest.skip('For some reason this interfers with the next test...')
    def test_added_account_is_then_returned_inside_a_query(self):
        # When
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        id = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.commit()
        account = self.query.filter_by(id=id).first()

        # Then
        self.assertEquals('facebook', account.type)

    def test_added_account_does_not_override_previously_created_ones(self):
        # When
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                                 type='facebook'))
        id = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.commit()
        account = self.query.filter_by(id=id).first()

        # Then
        self.assertNotEquals('aid', id)
        self.assertEquals('uid', account.user_id)
