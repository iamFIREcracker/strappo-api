#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Account
from app.models import User
from app.repositories.users import AccountsRepository


class TestAccountsRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = Account.query

    def tearDown(self):
        self.session.remove()

    def test_added_account_is_then_returned_inside_a_query(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()
        self.session.remove

        # When
        account = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.add(account)
        self.session.commit()
        account = self.query.filter_by(id=account.id).first()

        # Then
        self.assertEquals('facebook', account.type)

    def test_added_account_does_not_override_previously_created_ones(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Account(id='aid', user_id='uid', external_id='eid',
                                 type='facebook'))
        self.session.commit()
        self.session.remove()

        # When
        account = AccountsRepository.add('uid', 'eid', 'facebook')
        self.session.add(account)
        self.session.commit()
        account = self.query.filter_by(id=account.id).first()

        # Then
        self.assertNotEquals('aid', id)
        self.assertEquals('uid', account.user_id)
