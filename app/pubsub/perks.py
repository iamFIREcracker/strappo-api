#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub import Publisher
from app.pubsub import serialize_date


def _serialize_perk(gettext, perk):
    if perk is None:
        return None
    return dict(id=perk.perk.id,
                name=gettext("perk_name_%s" % perk.perk.name),
                description=gettext("perk_description_%s" % perk.perk.name),
                valid_until=serialize_date(perk.valid_until))


def serialize_driver_perk(gettext, driver_perk):
    return _serialize_perk(gettext, driver_perk)


def serialize_passenger_perk(gettext, passenger_perk):
    return _serialize_perk(gettext, passenger_perk)


class DriverPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('driver_perks_found',
                     perks_repository.active_driver_perks(user_id))


class PassengerPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('passenger_perks_found',
                     perks_repository.active_passenger_perks(user_id))
