#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class RideRequestCreator(Publisher):
    def perform(self, repository, driver_id, passenger_id):
        """Creates a ride request from driver identified by ``driver_id`` and
        passenger identified by ``passenger_id``.

        On success a 'request_created' message will be published toghether
        with the created request.
        """
        request = repository.add(driver_id, passenger_id)
        self.publish('ride_request_created', request)

