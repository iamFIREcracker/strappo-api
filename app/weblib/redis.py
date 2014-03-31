#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import redis
import web

__all__ = ['create_redis']


def create_redis(location=None):
    if location is None:
        location = web.config.get('REDIS_LOCATION', 'localhost')
    return redis.Redis(location)
