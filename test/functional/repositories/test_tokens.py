#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import Token
from app.models import User
from app.repositories.users import TokensRepository


class TestTokensRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        cls.session = Token.session
        cls.query = Token.query

    def setUp(self):
        pass

    def tearDown(self):
        Token.session.rollback()
        Token.session.remove()

    @unittest.skip('For some reason this interfers with the next test...')
    def test_added_token_is_then_returned_inside_a_query(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        token = TokensRepository.add('uid')
        self.session.add(token)
        self.session.commit()
        token = self.query.filter_by(id=token.id).first()

        # Then
        self.assertEquals('uid', token.user_id)

    def test_added_token_does_not_override_previously_created_ones(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        token = TokensRepository.add('uid')
        self.session.add(token)
        self.session.commit()
        token = self.query.filter_by(id=token.id).first()

        # Then
        self.assertNotEquals('tid', id)
        self.assertEquals('uid', token.user_id)
