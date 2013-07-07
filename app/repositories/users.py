#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Token
from app.models import User
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
    def add(acs_id, name, avatar):
        id = unicode(uuid.uuid4())
        user = User(id=id, acs_id=acs_id, name=name, avatar=avatar)
        return user

    @staticmethod
    def refresh_token(user_id):
        return TokensRepository.add(user_id)

    @staticmethod
    def authorized_by(token):
        return expunged(User.query.join(Token).filter(Token.id == token).\
                                filter(User.deleted == False).first(),
                        User.session)

    @staticmethod
    def with_acs_id(acs_id):
        return expunged(User.query.\
                                filter(User.acs_id == acs_id).\
                                filter(User.deleted == False).first(),
                        User.session)
