#!/usr/bin/env python
# -*- coding: utf-8 -*-


import uuid
from datetime import date
from datetime import timedelta

from app.models import Base
from app.models import ActiveDriverPerk
from app.models import ActivePassengerPerk
from app.models import EligibleDriverPerk
from app.models import EligiblePassengerPerk
from app.models import DriverPerk
from app.models import PassengerPerk
from app.weblib.db import and_
from app.weblib.db import expunged
from app.weblib.db import exists
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.expression import true


class PerksRepository(object):
    STANDARD_DRIVER_NAME = 'driver_standard'
    STANDARD_PASSENGER_NAME = 'passenger_standard'
    EARLY_BIRD_DRIVER_NAME = 'driver_early_bird'

    @staticmethod
    def _driver_perks_with_names(*names):
        return (DriverPerk.query.
                filter(DriverPerk.deleted == false()).
                filter(DriverPerk.name.in_(names)))

    @staticmethod
    def driver_perks_with_names(*names):
        return [expunged(p, Base.session)
                for p in PerksRepository._driver_perks_with_names(*names)]

    @staticmethod
    def _passenger_perks_with_names(*names):
        return (PassengerPerk.query.
                filter(PassengerPerk.deleted == false()).
                filter(PassengerPerk.name.in_(names)))

    @staticmethod
    def passenger_perks_with_names(*names):
        return [expunged(p, Base.session)
                for p in PerksRepository._passenger_perks_with_names(*names)]

    @staticmethod
    def add_driver_perk(name, eligible_for, active_for, fixed_rate,
                        multiplier):
        perk = DriverPerk(id=unicode(uuid.uuid4()),
                          deleted=False,
                          name=name,
                          eligible_for=eligible_for,
                          active_for=active_for,
                          fixed_rate=fixed_rate,
                          multiplier=multiplier)
        return perk

    @staticmethod
    def eligiblify_driver_perk(user, perk):
        valid_until = date.today() + timedelta(perk.eligible_for)
        return EligibleDriverPerk(id=unicode(uuid.uuid4()),
                                  deleted=False,
                                  user_id=user.id,
                                  perk_id=perk.id,
                                  valid_until=valid_until)

    @staticmethod
    def add_passenger_perk(name, eligible_for, active_for, fixed_rate,
                           multiplier):
        perk = PassengerPerk(id=unicode(uuid.uuid4()),
                             deleted=False,
                             name=name,
                             eligible_for=eligible_for,
                             active_for=active_for,
                             fixed_rate=fixed_rate,
                             multiplier=multiplier)
        return perk

    @staticmethod
    def eligiblify_passenger_perk(user, perk):
        valid_until = date.today() + timedelta(perk.eligible_for)
        return EligiblePassengerPerk(id=unicode(uuid.uuid4()),
                                     deleted=False,
                                     user_id=user.id,
                                     perk_id=perk.id,
                                     valid_until=valid_until)

    @staticmethod
    def _eligible_driver_perks(user_id):
        return (EligibleDriverPerk.query.options(joinedload('perk')).
                filter(EligibleDriverPerk.deleted == false()).
                filter(EligibleDriverPerk.user_id == user_id).
                filter(EligibleDriverPerk.valid_until >= date.today()).
                filter(~exists().
                       where(and_(ActiveDriverPerk.perk_id ==
                                  EligibleDriverPerk.perk_id,
                                  ActiveDriverPerk.user_id ==
                                  EligibleDriverPerk.user_id))).
                order_by(EligibleDriverPerk.created.desc()))

    @staticmethod
    def eligible_driver_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._eligible_driver_perks(user_id)]

    @staticmethod
    def _eligible_passenger_perks(user_id):
        return (EligiblePassengerPerk.query.options(joinedload('perk')).
                filter(EligiblePassengerPerk.deleted == false()).
                filter(EligiblePassengerPerk.user_id == user_id).
                filter(EligiblePassengerPerk.valid_until >= date.today()).
                filter(~exists().
                       where(and_(ActivePassengerPerk.perk_id ==
                                  EligiblePassengerPerk.id,
                                  ActivePassengerPerk.user_id ==
                                  EligiblePassengerPerk.user_id))).
                order_by(EligiblePassengerPerk.created.desc()))

    @staticmethod
    def eligible_passenger_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._eligible_passenger_perks(user_id)]

    @staticmethod
    def activate_driver_perk(user, perk):
        valid_until = date.today() + timedelta(perk.active_for)
        return ActiveDriverPerk(id=unicode(uuid.uuid4()),
                                deleted=False,
                                user_id=user.id,
                                perk_id=perk.id,
                                valid_until=valid_until)

    @staticmethod
    def activate_passenger_perk(user, perk):
        valid_until = date.today() + timedelta(perk.active_for)
        return ActivePassengerPerk(id=unicode(uuid.uuid4()),
                                   deleted=False,
                                   user_id=user.id,
                                   perk_id=perk.id,
                                   valid_until=valid_until)

    @staticmethod
    def _active_driver_perks(user_id):
        return (ActiveDriverPerk.query.options(joinedload('perk')).
                filter(ActiveDriverPerk.deleted == false()).
                filter(ActiveDriverPerk.user_id == user_id).
                filter(ActiveDriverPerk.valid_until >= date.today()).
                order_by(ActiveDriverPerk.created.desc()))

    @staticmethod
    def active_driver_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._active_driver_perks(user_id)]

    @staticmethod
    def active_driver_perks_without_standard_one(user_id):
        return (p for p in PerksRepository.active_driver_perks(user_id)
                if p.perk.name != PerksRepository.STANDARD_DRIVER_NAME)

    @staticmethod
    def _active_passenger_perks(user_id):
        return (ActivePassengerPerk.query.options(joinedload('perk')).
                filter(ActivePassengerPerk.deleted == false()).
                filter(ActivePassengerPerk.user_id == user_id).
                filter(ActivePassengerPerk.valid_until >= date.today()).
                order_by(ActivePassengerPerk.created.desc()))

    @staticmethod
    def active_passenger_perks(user_id):
        return [expunged(p, Base.session)
                for p in PerksRepository._active_passenger_perks(user_id)]

    @staticmethod
    def active_passenger_perks_without_standard_one(user_id):
        return (p for p in PerksRepository.active_passenger_perks(user_id)
                if p.perk.name != PerksRepository.STANDARD_PASSENGER_NAME)
