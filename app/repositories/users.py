#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import Account
from app.models import Token
from app.models import User


class UsersRepository(object):

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
