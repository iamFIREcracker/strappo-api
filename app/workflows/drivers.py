#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.drivers as driver_forms
from app.pubsub.drivers import DriverWithUserIdGetter
from app.pubsub.drivers import DriverUpdater
from app.pubsub.drivers import DriverSerializer
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class DriversWithUserIdWorkflow(Publisher):
    """Defines a workflow to view the details of a registered driver."""

    def perform(self, logger, repository, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithUserIdGetter()
        driver_serializer = DriverSerializer()

        class DriverWithUserIdGetterSubscriber(object):
            def driver_not_found(self, user_id):
                outer.publish('not_found', user_id)
            def driver_found(self, driver):
                driver_serializer.perform(driver)

        class DriverSerializerSubscriber(object):
            def driver_serialized(self, blob):
                outer.publish('driver_view', blob)


        driver_getter.add_subscriber(logger, DriverWithUserIdGetterSubscriber())
        driver_serializer.add_subscriber(logger, DriverSerializerSubscriber())
        driver_getter.perform(repository, user_id)


class EditDriverWorkflow(Publisher):
    """Defines a workflow to edit the details of a registered driver."""

    def perform(self, orm, logger, params, repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_updater = DriverUpdater()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
                orm.rollback()
            def valid_form(self, form):
                driver_updater.perform(repository, driver_id,
                                       form.d.license_plate,
                                       form.d.telephone)

        class DriverUpdaterSubscriber(object):
            def driver_not_found(self, driver_id):
                orm.rollback()
                outer.publish('not_found', driver_id)
            def driver_updated(self, driver):
                orm.add(driver)
                orm.commit()
                outer.publish('updated', driver)

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_updater.add_subscriber(logger, DriverUpdaterSubscriber())
        form_validator.perform(driver_forms.update(), params,
                               describe_invalid_form)
