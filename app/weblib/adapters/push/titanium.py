#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib
import urllib2

import web


class TitaniumPushNotificationsAdapter(object):
    """Defines an adapter of the Titanium push notification system."""

    NOTIFY_TOKENS_URL = 'https://api.cloud.appcelerator.com/v1/push_notification/notify_tokens.json'

    def notify_tokens(self, channel, tokens, payload):
        data = urllib.urlencode(dict(key=web.config.TITANIUM_KEY,
                                     channel=channel,
                                     to_tokens=','.join(tokens),
                                     payload=payload))
        req = urllib2.Request(self.NOTIFY_TOKENS_URL, data)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server',
                           self.NOTIFY_TOKENS_URL, data))
        try:
            payload = json.load(response)
            if payload['meta']['status'] == 'ok':
                return (None, None)
        except Exception as e:
            return (None, e)

