#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Passenger
from app.models import User
from app.weblib.db import expunged


class PassengersRepository(object):
    @staticmethod
    def get(id):
        return expunged(Passenger.query.join(User).\
                                filter(Passenger.id == id).\
                                filter(User.deleted == False).first(),
                        Passenger.session)

    @staticmethod
    def get_all_active():
        return [expunged(p, Passenger.session)
                for p in Passenger.query.join(User).\
                        filter(User.deleted == False).\
                        filter(Passenger.active == True)]

    @staticmethod
    def add(user_id, origin, destination, buddies):
        id = unicode(uuid.uuid4())
        passenger = Passenger(id=id, user_id=user_id, origin=origin,
                              destination=destination, buddies=buddies,
                              active=True)
        return passenger

