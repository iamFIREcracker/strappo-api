#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Passenger
from app.models import RideRequest
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
    def get_all_accepted_by_driver(driver_id):
        """Returns all the _accepted_ passengers, currently in _active_ state.

        A passenger is considered _accepted_ if a ``RideRequest`` exists with
        'accepted' equal to ``True`` and 'passenger_id' equal to the passenger
        ID;  on the other hand, a passenger is marked as active if its 'active'
        property is equal to ``True`` (i.e. it is still the same day in which
        the passenger record has been added to the system.
        """
        return [expunged(p, Passenger.session)
                for p in Passenger.query.options(joinedload('user')).\
                        join(RideRequest).\
                        filter(User.deleted == False).\
                        filter(RideRequest.driver_id == driver_id).\
                        filter(RideRequest.accepted == True).\
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
