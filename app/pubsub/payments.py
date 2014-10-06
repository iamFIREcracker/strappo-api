#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


def reimbursement_for(fixed_rate, multiplier, seats, per_seat_cost,
                      distance, per_distance_unit_cost):
    return fixed_rate + \
        multiplier * (seats * per_seat_cost) * \
        (distance * per_distance_unit_cost)


class ReimbursementCalculator(Publisher):
    def perform(self, fixed_rate, multiplier, seats, per_seat_cost,
                distance, per_distance_unit_cost):
        self.publish('reimbursement_calculated',
                     reimbursement_for(fixed_rate, multiplier,
                                       seats, per_seat_cost,
                                       distance, per_distance_unit_cost))


def fare_for(fixed_rate, multiplier, seats, per_seat_cost,
             distance, per_distance_unit_cost):
    return fixed_rate + \
        multiplier * (seats * per_seat_cost) * \
        (distance * per_distance_unit_cost)


class FareCalculator(Publisher):
    def perform(self, fixed_rate, multiplier, seats, per_seat_cost,
                distance, per_distance_unit_cost):
        self.publish('fare_calculated',
                     fare_for(fixed_rate, multiplier,
                              seats, per_seat_cost,
                              distance, per_distance_unit_cost))


class ReimbursementCreator(Publisher):
    def perform(self, payments_repository, drive_request_id, driver_id,
                credits_):
        self.publish('reimbursement_created',
                     payments_repository.add(drive_request_id, None,
                                             driver_id, credits_))


class FareCreator(Publisher):
    def perform(self, payments_repository, drive_request_id, passenger_id,
                credits_):
        self.publish('fare_created',
                     payments_repository.add(drive_request_id, passenger_id,
                                             None, credits_))
