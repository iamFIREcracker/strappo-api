#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Account
from app.models import Token
from app.models import User
from app.repositories.accounts import AccountsRepository
from app.repositories.tokens import TokensRepository


class UsersRepository(object):

    @staticmethod
    def add(name, phone, avatar):
        id = unicode(uuid.uuid4())
        user = User(id=id, name=name, phone=phone, avatar=avatar)
        User.session.add(user)
        return id

    @staticmethod
    def refresh_account(user_id, external_id, account_type):
        return AccountsRepository.add(user_id, external_id, account_type)

    @staticmethod
    def refresh_token(user_id):
        return TokensRepository.add(user_id)

    @staticmethod
    def authorized_by(token):
        return User.query.join(Token).filter(Token.id == token).\
                filter(User.deleted == False).first()

    @staticmethod
    def with_account(external_id, account_type):
        return User.query.join(Account).\
                filter(Account.external_id == external_id).\
                filter(Account.type == account_type).\
                filter(User.deleted == False).first()
