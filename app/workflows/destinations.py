#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.destinations import DestinationsGetter
from app.pubsub.destinations import MultipleDestinationsSerializer
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class ListDestinationsWorkflow(Publisher):
    """Defines a workflow to retrieve the list of passengers destinations."""

    def perform(self, logger, repository_method):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        destinations_getter = DestinationsGetter()
        destinations_serializer = MultipleDestinationsSerializer()

        class DestinationsGetterSubscriber(object):
            def destinations_found(self, destinations):
                destinations_serializer.perform(destinations)

        class DestinationsSerializerSubscriber(object):
            def destinations_serialized(self, blob):
                outer.publish('success', blob)


        destinations_getter.add_subscriber(logger,
                                           DestinationsGetterSubscriber())
        destinations_serializer.add_subscriber(logger,
                                               DestinationsSerializerSubscriber())
        destinations_getter.perform(repository_method)
