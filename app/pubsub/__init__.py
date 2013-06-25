#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class DeviceTokensNotifier(Publisher):
    def perform(self, push_adapter, channel, device_tokens, payload):
        """Invoke the ``notify_tokens`` method of the push notifications adapter
        and publish result messages accordingly.

        On success, a 'device_tokens_not_notified' message is published, while
        if something bad happens, a 'device_tokens_not_notified' message will be
        sent back to subscribers.
        """
        (_, error) = push_adapter.notify_tokens(channel, device_tokens, payload)
        if error:
            self.publish('device_tokens_not_notified', error)
        else:
            self.publish('device_tokens_notified')
