#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.pubsub.drivers import DriverGetter
from app.pubsub.drivers import DriverSerializer
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class ViewDriverWorkflow(Publisher):
    """Defines a workflow to view the details of a registered driver."""

    def perform(self, logger, repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverGetter()
        driver_serializer = DriverSerializer()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                driver_serializer.perform(driver)

        class DriverSerializerSubscriber(object):
            def driver_serialized(self, blob):
                outer.publish('driver_view', blob)


        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_serializer.add_subscriber(logger, DriverSerializerSubscriber())
        driver_getter.perform(repository, driver_id)
