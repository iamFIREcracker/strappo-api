#!/usr/bin/env python

import datetime
import json

from web.session import Store


def _id(key):
    return 'webpy.' + key


class RedisStore(Store):
    def __init__(self, redis):
        self._redis = redis

    def __contains__(self, key):
        return self._redis.get(_id(key)) is not None

    def __getitem__(self, key):
        value = json.loads(self._redis.get(_id(key)))[0]
        self[key] = value
        return value

    def __setitem__(self, key, value):
        data = json.dumps([value, str(datetime.datetime.now())])
        self._redis.set(_id(key), data)

    def __delitem__(self, key):
        self._redis.delete(_id(key))

    def cleanup(self, timeout):
        # XXX implement this
        pass
