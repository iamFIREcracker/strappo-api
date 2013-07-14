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
    def perform(self, repository, user_id, origin, destination, seats):
        """Creates a new passenger with the specified set of properties.

        On success a 'passenger_created' message will be published toghether
        with the created user.
        """
        passenger = repository.add(user_id, origin, destination, seats)
        self.publish('passenger_created', passenger)


class PassengerWithUserIdAuthorizer(Publisher):
    def perform(self, user_id, passenger):
        """Checkes if the 'user_id' property of the given passenger record
        matches the given user ID.

        An 'authorized' message is published if the given user ID is equal to
        the one associated with the given passenger;  otherwise, an
        'unauthorized' message is sent back to subscribers.
        """
        entitled = user_id == passenger.user_id
        if entitled:
            self.publish('authorized', user_id, passenger)
        else:
            self.publish('unauthorized', user_id, passenger)


def serialize(passenger):
    if passenger is None:
        return None
    return dict(id=passenger.id, origin=passenger.origin,
                destination=passenger.destination, seats=passenger.seats)


def _serialize(passenger):
    from app.pubsub.users import serialize as serialize_user
    d = serialize(passenger)
    d.update(user=serialize_user(passenger.user))
    return d


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


class MultiplePassengersDeactivator(Publisher):
    def perform(self, passengers):
        """Hides the list of provided passengers.

        At the end of the operation, a 'passengers_hid' message will be
        published, toghether with the list of modified passengers.
        """
        def deactivate(p):
            p.active = False
            return p
        self.publish('passengers_hid', [deactivate(p) for p in passengers])


class PassengerACSUserIdExtractor(Publisher):
    def perform(self, passenger):
        """Extract ACS user ID associated with the given passenger.

        At the end of the operation a 'acs_user_id_extracted' message will be
        published, together with the ACS user id of the passenger.
        """
        self.publish('acs_user_id_extracted', passenger.user.acs_id)
