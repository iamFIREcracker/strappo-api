#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.pubsub.passengers import AllPassengersGetter
from app.pubsub.passengers import MultiplePassengersSerializer
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class PassengersWorkflow(Publisher):
    """Defines a workflow to view the list of active passengers."""

    def perform(self, logger, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = AllPassengersGetter()
        passengers_serializer = MultiplePassengersSerializer()

        class AllPassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_serializer.perform(passengers)

        class PassengersSerializerSubscriber(object):
            def passengers_serialized(self, blob):
                outer.publish('success', blob)


        passengers_getter.add_subscriber(logger,
                                         AllPassengersGetterSubscriber())
        passengers_serializer.add_subscriber(logger,
                                             PassengersSerializerSubscriber())
        passengers_getter.perform(repository)
