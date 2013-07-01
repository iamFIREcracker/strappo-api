#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Passenger
from app.models import User
from app.weblib.db import expunged
from app.weblib.db import joinedload


class PassengersRepository(object):
    @staticmethod
    def get(id):
        return expunged(Passenger.query.options(joinedload('user')).\
                                filter(User.deleted == False).\
                                filter(Passenger.id == id).first(),
                        Passenger.session)

    @staticmethod
    def get_all_active():
        return [expunged(p, Passenger.session)
                for p in Passenger.query.options(joinedload('user')).\
                        filter(User.deleted == False).\
                        filter(Passenger.active == True)]

    @staticmethod
    def add(user_id, origin, destination, seats):
        id = unicode(uuid.uuid4())
        passenger = Passenger(id=id, user_id=user_id, origin=origin,
                              destination=destination, seats=seats,
                              active=True)
        return passenger

    @staticmethod
    def deactivate(passenger_id):
        passenger = PassengersRepository.get(passenger_id)
        if passenger is None:
            return None
        else:
            passenger.active = False
            return passenger
