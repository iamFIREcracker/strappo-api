#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class DestinationsGetter(Publisher):
    def perform(self, repository_method):
        """Search for all the active passenger destinations.

        When done, a 'destinations_found' message will be published, followed by
        the list of active destinations.
        """
        self.publish('destinations_found', repository_method())


def _serialize(d):
    return d[0]


class MultipleDestinationsSerializer(Publisher):
    def perform(self, destinations):
        """Convert a list of destinations into serializable objects.

        At the end of the operation, the method will emit a
        'destinations_serialized' message containing serialized objects.
        """
        self.publish('destinations_serialized',
                     [_serialize(d) for d in destinations])
