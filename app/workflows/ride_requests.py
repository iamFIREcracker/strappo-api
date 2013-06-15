#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.ride_requests import RideRequestCreator
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher


class AddRideRequestWorkflow(Publisher):
    """Defines a workflow to accept a passenger."""

    def perform(self, orm, logger, repository, driver_id, passenger_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        request_creator = RideRequestCreator()

        class RideRequestCreatorSubscriber(object):
            def ride_request_created(self, request):
                orm.add(request)
                outer.publish('success')

        request_creator.add_subscriber(logger, RideRequestCreatorSubscriber())
        request_creator.perform(repository, driver_id, passenger_id)
