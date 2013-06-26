#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.celery import celery

from app.weblib.logging import create_logger
from app.weblib.pubsub import Future
from app.repositories.drivers import DriversRepository
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.adapters.push.titanium import TitaniumPushNotificationsAdapter
from app.workflows.drivers import NotifyDriversWorkflow


@celery.task
def NotifyDriversTask(passenger_id):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_drivers = NotifyDriversWorkflow()
    ret = Future()

    class NotifyDriversSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_drivers.add_subscriber(logging_subscriber,
                                    NotifyDriversSubscriber())
    notify_drivers.perform(logger, DriversRepository, push_adapter,
                           'drivers', passenger_id) # XXX TBD payload
    return ret.get()
