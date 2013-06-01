#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import User


class UsersRepository(object):

    @staticmethod
    def get(userid):
        """Get the user identified by ``userid`` or None otherwise."""
        return User.query.filter_by(id=userid, deleted=False).first()
