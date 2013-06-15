#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class PassengerWithIdGetter(Publisher):
    def perform(self, repository, passenger_id):
        """Get the passenger identified by ``passenger_id``.

        If such passenger exists, a 'passenger_found' message is published
        containing the passenger details;  on the other hand, if no passenger
        exists with the specified ID, a 'passenger_not_found' message will be
        published
        """
        passenger = repository.get(passenger_id)
        if passenger is None:
            self.publish('passenger_not_found', passenger_id)
        else:
            self.publish('passenger_found', passenger)


class ActivePassengersGetter(Publisher):
    def perform(self, repository):
        """Search for all the active passengers around.

        When done, a 'passengers_found' message will be published, followed by
        the list of active passengers.
        """
        self.publish('passengers_found', repository.get_all_active())


class PassengerCreator(Publisher):
    def perform(self, repository, user_id, origin, destination, buddies):
        """Creates a new passenger with the specified set of properties.

        On success a 'passenger_created' message will be published toghether
        with the created user.
        """
        passenger = repository.add(user_id, origin, destination, buddies)
        self.publish('passenger_created', passenger)


def _serialize(p):
    return dict(id=p.id, origin=p.origin, destination=p.destination,
                buddies=p.buddies)


class PassengerSerializer(Publisher):
    def perform(self, passenger):
        """Convert the given passenger into a serializable dictionary.

        At the end of the operation the method will emit a
        'passenger_serialized' message containing the serialized object (i.e.
        passenger dictionary).
        """
        self.publish('passenger_serialized', _serialize(passenger))


class MultiplePassengersSerializer(Publisher):
    def perform(self, passengers):
        """Convert a list of passengers into serializable dictionaries.

        At the end of the operation, the method will emit a
        'passengers_serialized' message containing serialized objects.
        """
        self.publish('passengers_serialized',
                     [_serialize(p) for p in passengers])
