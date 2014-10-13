#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub import Publisher
from app.pubsub import serialize_date


def _serialize_perk(gettext, perk):
    if perk is None:
        return None
    return dict(name=gettext("perk_name_%s" % perk.name),
                description=gettext("perk_description_%s" % perk.name))


def _serialize_eligible_perk(gettext, perk):
    if perk is None:
        return None
    data = _serialize_perk(gettext, perk.perk)
    data.update(valid_until=serialize_date(perk.valid_until))
    return data


def _serialize_active_perk(gettext, perk):
    if perk is None:
        return None
    data = _serialize_perk(gettext, perk.perk)
    data.update(valid_until=serialize_date(perk.valid_until))
    return data


def serialize_eligible_driver_perk(gettext, driver_perk):
    return _serialize_eligible_perk(gettext, driver_perk)


def serialize_active_driver_perk(gettext, driver_perk):
    return _serialize_active_perk(gettext, driver_perk)


def serialize_eligible_passenger_perk(gettext, passenger_perk):
    return _serialize_eligible_perk(gettext, passenger_perk)


def serialize_active_passenger_perk(gettext, passenger_perk):
    return _serialize_active_perk(gettext, passenger_perk)


class ActiveDriverPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('active_driver_perks_found',
                     perks_repository.active_driver_perks(user_id))


class ActivePassengerPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('active_passenger_perks_found',
                     perks_repository.active_passenger_perks(user_id))
