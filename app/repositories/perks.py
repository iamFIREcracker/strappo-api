#!/usr/bin/env python
# -*- coding: utf-8 -*-


import uuid
from datetime import date
from datetime import timedelta

from app.models import Base
from app.models import ActiveDriverPerk
from app.models import ActivePassengerPerk
from app.models import DriverPerk
from app.models import PassengerPerk
from app.weblib.db import and_
from app.weblib.db import expunged
from app.weblib.db import exists
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.expression import true


class PerksRepository(object):
    @staticmethod
    def add_driver_perk(name, duration, fixed_rate, multiplier, per_seat_cost,
                        per_distance_unit_cost):
        perk = DriverPerk(id=unicode(uuid.uuid4()),
                          deleted=False,
                          name=name,
                          duration=duration,
                          fixed_rate=fixed_rate,
                          multiplier=multiplier,
                          per_seat_cost=per_seat_cost,
                          per_distance_unit_cost=per_distance_unit_cost)
        return perk

    @staticmethod
    def add_passenger_perk(name, duration, fixed_rate, multiplier,
                           per_seat_cost, per_distance_unit_cost):
        perk = PassengerPerk(id=unicode(uuid.uuid4()),
                             deleted=False,
                             name=name,
                             duration=duration,
                             fixed_rate=fixed_rate,
                             multiplier=multiplier,
                             per_seat_cost=per_seat_cost,
                             per_distance_unit_cost=per_distance_unit_cost)
        return perk

    @staticmethod
    def _eligible_driver_perks(user_id):
        return (DriverPerk.query.
                filter(DriverPerk.deleted == false()).
                filter(~exists().
                       where(and_(ActiveDriverPerk.perk_id == DriverPerk.id,
                                  ActiveDriverPerk.user_id == user_id))).
                limit(1))

    @staticmethod
    def eligible_driver_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._eligible_driver_perks(user_id)]

    @staticmethod
    def _eligible_passenger_perks(user_id):
        return (PassengerPerk.query.
                filter(PassengerPerk.deleted == false()).
                filter(~exists().
                       where(and_(ActivePassengerPerk.perk_id ==
                                  PassengerPerk.id,
                                  ActivePassengerPerk.user_id ==
                                  user_id))).
                limit(1))

    @staticmethod
    def eligible_passenger_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._eligible_passenger_perks(user_id)]


class ActivePerksRepository(object):
    @staticmethod
    def activate_driver_perk(user, perk):
        valid_until = date.today() + timedelta(perk.duration)
        return ActiveDriverPerk(id=unicode(uuid.uuid4()),
                                deleted=False,
                                user_id=user.id,
                                perk_id=perk.id,
                                valid_until=valid_until)

    @staticmethod
    def activate_passenger_perk(user, perk):
        valid_until = date.today() + timedelta(perk.duration)
        return ActivePassengerPerk(id=unicode(uuid.uuid4()),
                                   deleted=False,
                                   user_id=user.id,
                                   perk_id=perk.id,
                                   valid_until=valid_until)

    @staticmethod
    def _active_driver_perks(user_id):
        return (ActiveDriverPerk.query.options(joinedload('perk')).
                filter(ActiveDriverPerk.user_id == user_id).
                filter(ActiveDriverPerk.deleted == false()).
                limit(1))

    @staticmethod
    def active_driver_perks(user_id):
        return [expunged(p, Base.session)
                for p in ActivePerksRepository._active_driver_perks(user_id)]

    @staticmethod
    def _active_passenger_perks(user_id):
        return (ActivePassengerPerk.query.options(joinedload('perk')).
                filter(ActivePassengerPerk.user_id == user_id).
                filter(ActivePassengerPerk.deleted == false()).
                limit(1))

    @staticmethod
    def active_passenger_perks(user_id):
        return [expunged(p, Base.session)
                for p in ActivePerksRepository.
                _active_passenger_perks(user_id)]
