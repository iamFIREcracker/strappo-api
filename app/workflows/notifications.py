#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.notifications import NotificationsResetter

from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher


class ResetNotificationsWorkflow(Publisher):
    def perform(self, logger, redis, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        notifications_resetter = NotificationsResetter()

        class NotificationsResetterSubscriber(object):
            def notifications_reset(self, recordid):
                outer.publish('success')

        notifications_resetter.add_subscriber(logger,
                                              NotificationsResetterSubscriber())
        notifications_resetter.perform(redis, user_id)
