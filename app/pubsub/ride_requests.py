#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class RideRequestCreator(Publisher):
    def perform(self, repository, driver_id, passenger_id):
        """Creates a ride request from driver identified by ``driver_id`` and
        passenger identified by ``passenger_id``.

        On success a 'ride_request_created' message will be published toghether
        with the created request.
        """
        request = repository.add(driver_id, passenger_id)
        self.publish('ride_request_created', request)


class RideRequestAcceptor(Publisher):
    def perform(self, repository, driver_id, passenger_id):
        """Marks the ride request between driver identified by ``driver_id`` and
        the passenger identified by ``passenger_id`` as _accepted_.

        On success a 'ride_request_accepted' message with the accepted ride
        request object will be published;  on the other hand a
        'ride_request_not_found' message will be generated.
        """
        request = repository.accept(driver_id, passenger_id)
        if request is None:
            self.publish('ride_request_not_found', driver_id, passenger_id)
        else:
            self.publish('ride_request_accepted', request)
