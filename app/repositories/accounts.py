#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Account
from app.models import User


class AccountsRepository(object):

    @staticmethod
    def add(user_id, external_id, account_type):
        id = unicode(uuid.uuid4())
        account = Account(id=id, user_id=user_id, external_id=external_id,
                          type=account_type)
        Account.session.add(account)
        return id

    @staticmethod
    def get(user_id, external_id, account_type):
        return Account.query.join(User).\
                filter(Account.user_id == user_id).\
                filter(Account.external_id == external_id).\
                filter(Account.type == account_type).\
                filter(User.deleted == False).first()
