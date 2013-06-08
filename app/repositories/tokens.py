#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Token


class TokensRepository(object):

    @staticmethod
    def add(user_id):
        id = unicode(uuid.uuid4())
        token = Token(id=id, user_id=user_id)
        return token
