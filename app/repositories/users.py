#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import User
from app.models import Token


class UsersRepository(object):

    @staticmethod
    def authorized_by(token):
        return User.query.join(Token).filter(Token.id == token).\
                filter(User.deleted == False).first()
