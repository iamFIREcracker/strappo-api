#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import pi
from math import sqrt
from math import radians
from math import cos

from app.weblib.pubsub import Publisher


class ACSSessionCreator(Publisher):
    def perform(self, push_adapter):
        """Log into the Appcelerator Cloud services and return the created
        session.

        On success, an 'acs_session_created' message will be published,
        together with the session ID;  on failure, an 'acs_session_not_created'
        will be sent back to subscribers.
        """
        (session_id, error) = push_adapter.login()
        if error:
            self.publish('acs_session_not_created', error)
        else:
            self.publish('acs_session_created', session_id)

class ACSUserIdsNotifier(Publisher):
    def perform(self, push_adapter, session_id, channel, user_ids, payload):
        """Invoke the ``notify`` method of the push notifications adapter
        and then publish result messages accordingly.

        On success, a 'acs_user_ids_notified' message is published, while
        if something bad happens, a 'acs_user_ids_not_notified' message will be
        sent back to subscribers.
        """
        (_, error) = push_adapter.notify(session_id, channel, user_ids, payload)
        if error:
            self.publish('acs_user_ids_not_notified', error)
        else:
            self.publish('acs_user_ids_notified')

class ACSPayloadsForUserIdNotifier(Publisher):
    def perform(self, push_adapter, session_id, channel, tuples):
        errors = []
        for (user_id, payload) in tuples:
            (_, error) = push_adapter.notify(session_id, channel,
                                             [user_id], payload)
            if error:
                errors += [error]
        if errors:
            self.publish('acs_user_ids_not_notified', errors)
        else:
            self.publish('acs_user_ids_notified')


class PayloadsByUserCreator(Publisher):
    def perform(self, payload_factory, users):
        self.publish('payloads_created',
                     [payload_factory(u) for u in users])


EARTH_RADIUS = 6371.009
KM_PER_DEG_LAT = 2 * pi * EARTH_RADIUS / 360.0

def distance(lat1, lon1, lat2, lon2):
    km_per_deg_lon = KM_PER_DEG_LAT * cos(radians(lat1))
    return sqrt((KM_PER_DEG_LAT * (lat1 - lat2)) ** 2 +
                (km_per_deg_lon * (lon1 - lon2)) ** 2)


class DistanceCalculator(Publisher):
    def perform(self, lat1, lon1, lat2, lon2):
        self.publish('distance_calculated', distance(lat1, lon1, lat2, lon2))


def serialize_date(date):
    if date is None:
        return None
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')
