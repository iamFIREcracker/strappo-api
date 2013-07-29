#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib
import urllib2

import web


class TitaniumPushNotificationsAdapter(object):
    """Defines an adapter of the Titanium push notification system."""

    LOGIN_URL = 'https://api.cloud.appcelerator.com/v1/users/login.json?key=%(key)s'

    def login(self):
        url = self.LOGIN_URL % dict(key=web.config.TITANIUM_KEY)
        req = urllib2.Request(url)
        data = urllib.urlencode(dict(login=web.config.TITANIUM_LOGIN,
                                     password=web.config.TITANIUM_PASSWORD))
        try:
            response = urllib2.urlopen(req, data)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server', url, data, str(e)))
        else:
            return (json.load(response)['meta']['session_id'], None)

    NOTIFY_URL = 'https://api.cloud.appcelerator.com/v1/push_notification/notify.json?key=%(key)s'

    def notify(self, session_id, channel, ids, payload):
        # Do not call ACS if the list of user IDs to notify is empty, otherwise
        # a broadcast message will be sent
        if not ids:
            return ('Skipped, empty `ids` list', None)

        url = self.NOTIFY_URL % dict(key=web.config.TITANIUM_KEY)
        session_cookie = '_session_id=%(id)s' % dict(id=session_id)
        req = urllib2.Request(url)
        req.add_header('Cookie', session_cookie)
        data = urllib.urlencode(dict(channel=channel,
                                     to_ids=','.join(ids),
                                     payload=payload))
        try:
            response = urllib2.urlopen(req, data)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server', url, data, str(e)))
        else:
            return (response, None)
