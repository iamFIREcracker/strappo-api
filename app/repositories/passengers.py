#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import Passenger
from app.models import User
from app.weblib.db import expunged


class PassengersRepository(object):
    @staticmethod
    def get_all():
        return [expunged(p, Passenger.session)
                for p in Passenger.query.join(User).\
                        filter(User.deleted == False)]
