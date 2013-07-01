#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class ACSUserIdsNotifier(Publisher):
    def perform(self, push_adapter, channel, user_ids, payload):
        """Invoke the ``notify`` method of the push notifications adapter
        and then publish result messages accordingly.

        On success, a 'acs_user_ids_notified' message is published, while
        if something bad happens, a 'acs_user_ids_not_notified' message will be
        sent back to subscribers.
        """
        (_, error) = push_adapter.notify(channel, user_ids, payload)
        if error:
            self.publish('acs_user_ids_not_notified', error)
        else:
            self.publish('acs_user_ids_notified')
