#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Account
from app.models import Token
from app.models import User
from app.repositories.accounts import AccountsRepository
from app.repositories.tokens import TokensRepository
from app.weblib.db import expunged
from app.weblib.db import joinedload


class UsersRepository(object):
    @staticmethod
    def get(id):
        return expunged(User.query.options(joinedload('driver'),
                                           joinedload('passenger')).\
                                filter(User.deleted == False).\
                                filter(User.id == id).first(),
                        User.session)

    @staticmethod
    def add(name, avatar):
        id = unicode(uuid.uuid4())
        user = User(id=id, name=name, avatar=avatar)
        return user

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
