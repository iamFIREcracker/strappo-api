#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub import Publisher
from app.pubsub import serialize_date


def _serialize_perk(perk):
    if perk is None:
        return None
    return dict(id=perk.perk.id,
                name=perk.perk.name,
                multiplier=perk.perk.multiplier,
                per_seat_cost=perk.perk.per_seat_cost,
                per_distance_unit_cost=perk.perk.per_distance_unit_cost,
                valid_until=serialize_date(perk.valid_until))


def serialize_driver_perk(driver_perk):
    return _serialize_perk(driver_perk)


def serialize_passenger_perk(passenger_perk):
    return _serialize_perk(passenger_perk)


class DriverPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('driver_perks_found',
                     perks_repository.active_driver_perks(user_id))


class PassengerPerksGetter(Publisher):
    def perform(self, perks_repository, user_id):
        self.publish('passenger_perks_found',
                     perks_repository.active_passenger_perks(user_id))
