#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


class PayloadsByLocaleCreator(Publisher):
    def perform(self, payload_factory, locales):
        self.publish('payloads_created',
                     [payload_factory(l) for l in locales])
