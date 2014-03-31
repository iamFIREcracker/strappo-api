#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher

def notificationid_for_user(user_id):
    return "notifications.%s" % (user_id,)


class NotificationsResetter(Publisher):
    def perform(self, redis, user_id):
        recordid = notificationid_for_user(user_id)
        redis.set(recordid, 0)
        self.publish('notifications_reset', recordid)
