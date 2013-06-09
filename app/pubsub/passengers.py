#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class AllPassengersGetter(Publisher):
    def perform(self, repository):
        """Search for all the active passengers around.

        When done, a 'passengers_found' message will be published, followed by
        the list of active passengers.
        """
        self.publish('passengers_found', repository.get_all())


class MultiplePassengersSerializer(Publisher):
    def perform(self, passengers):
        """Convert a list of passengers into serializable dictionaries.

        At the end of the operation, the method will emit a
        'passengers_serialized' message containing serialized objects.
        """
        self.publish('passengers_serialized',
                     [dict(id=p.id, user_id=p.user_id, origin=p.origin,
                           destination=p.destination, buddies=p.buddies,
                           name=p.user.name, avatar=p.user.avatar)
                      for p in passengers])
