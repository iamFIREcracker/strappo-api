#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2

import web


class TitaniumPushNotificationsAdapter(object):
    """Defines an adapter of the Titanium push notification system."""

    LOGIN_URL = 'https://api.cloud.appcelerator.com/v1/users/login.json?key=%(key)s'

    def login(self):
        url = self.NOTIFY_URL % dict(key=web.config.TITANIUM_KEY)
        data = urllib.urlencode(dict(login=web.config.TITANIUM_LOGIN,
                                     password=web.config.TITANIUM_PASSWORD))
        try:
            response = urllib2.urlopen(url, data)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server', url, data, str(e)))
        else:
            return (response, None)

    NOTIFY_URL = 'https://api.cloud.appcelerator.com/v1/push_notification/notify.json?key=%(key)s'

    def notify(self, channel, ids, payload):
        url = self.NOTIFY_URL % dict(key=web.config.TITANIUM_KEY)
        data = urllib.urlencode(dict(channel=channel,
                                     to_ids=','.join(ids),
                                     payload=payload))
        try:
            response = urllib2.urlopen(url, data)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server', url, data, str(e)))
        else:
            return (response, None)
