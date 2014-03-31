#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class NotificationsResetter(Publisher):
    def perform(self, redis, user_id):
        recordid = "notifications.%s" % (user_id,)
        redis.set(recordid, 0)
        self.publish('notifications_reset', recordid)
