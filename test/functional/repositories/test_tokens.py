#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Token
from app.models import User
from app.repositories.users import TokensRepository


class TestTokensRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = Token.query

    def tearDown(self):
        self.session.remove()

    def test_added_token_is_then_returned_inside_a_query(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()
        self.session.remove()

        # When
        token = TokensRepository.add('uid')
        self.session.add(token)
        self.session.commit()
        token = self.query.filter_by(id=token.id).first()

        # Then
        self.assertEquals('uid', token.user_id)

    def test_added_token_does_not_override_previously_created_ones(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Token(id='tid', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        token = TokensRepository.add('uid')
        self.session.add(token)
        self.session.commit()
        token = self.query.filter_by(id=token.id).first()

        # Then
        self.assertNotEquals('tid', id)
        self.assertEquals('uid', token.user_id)
