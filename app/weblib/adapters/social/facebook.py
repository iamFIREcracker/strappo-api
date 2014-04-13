#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2


class FacebookAdapter(object):
    """Defines a tiny adapter of the Facebook Graph API."""

    PROFILE = 'https://graph.facebook.com/me?access_token=%(token)s'

    def profile(self, access_token):
        url = self.PROFILE % dict(token=access_token)
        try:
            return (json.load(urllib2.urlopen(url)), None)
        except urllib2.HTTPError as e:
            return (None, ('Unable to contact the server', url, str(e)))

    AVATAR = 'https://graph.facebook.com/%(id)s/picture?width=200&height=200'

    def name(self, first_name, last_name):
        if last_name:
            last_name = last_name[0] + '.'
        return ' '.join([first_name, last_name])

    def avatar(self, user_id):
        return self.AVATAR % dict(id=user_id)
