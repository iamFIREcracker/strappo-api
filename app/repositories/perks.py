#!/usr/bin/env python
# -*- coding: utf-8 -*-


import uuid
from datetime import date
from datetime import timedelta

from app.models import Base
from app.models import DriverPerk
from app.models import PassengerPerk
from app.models import Perk
from app.weblib.db import expunged
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.expression import true


class PerksRepository(object):
    @staticmethod
    def add(name, duration, fixed_rate, multiplier, per_seat_cost,
            per_distance_unit_cost):
        perk = Perk(id=unicode(uuid.uuid4()),
                    deleted=False,
                    name=name,
                    duration=duration,
                    fixed_rate=fixed_rate,
                    multiplier=multiplier,
                    per_seat_cost=per_seat_cost,
                    per_distance_unit_cost=per_distance_unit_cost)
        return perk

    @staticmethod
    def add_driver_perk(user, perk):
        valid_until = date.today() + timedelta(perk.duration)
        return DriverPerk(id=unicode(uuid.uuid4()),
                          deleted=False,
                          user_id=user.id,
                          perk_id=perk.id,
                          valid_until=valid_until)

    @staticmethod
    def add_passenger_perk(user, perk):
        valid_until = date.today() + timedelta(perk.duration)
        return PassengerPerk(id=unicode(uuid.uuid4()),
                             deleted=False,
                             user_id=user.id,
                             perk_id=perk.id,
                             valid_until=valid_until)

    @staticmethod
    def _active_driver_perks(user_id):
        return (DriverPerk.query.options(joinedload('perk')).
                filter(DriverPerk.user_id == user_id).
                filter(DriverPerk.deleted == false()).
                limit(1))

    @staticmethod
    def active_driver_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._active_driver_perks(user_id)]

    @staticmethod
    def _active_passenger_perks(user_id):
        return (PassengerPerk.query.options(joinedload('perk')).
                filter(PassengerPerk.user_id == user_id).
                filter(PassengerPerk.deleted == false()).
                limit(1))

    @staticmethod
    def active_passenger_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._active_passenger_perks(user_id)]


if __name__ == '__main__':
    print PerksRepository.active_driver_perks('aaf5d3a4-3465-46e8-b356-74cb158231e8')
    print PerksRepository.active_passenger_perks('aaf5d3a4-3465-46e8-b356-74cb158231e8')
