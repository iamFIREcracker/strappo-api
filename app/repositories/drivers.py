#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import User
from app.models import Driver


class DriversRepository(object):

    @staticmethod
    def get(user_id):
        return Driver.query.join(User).\
                filter(User.id == user_id).\
                filter(User.deleted == False).first()
