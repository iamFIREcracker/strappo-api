#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.drivers as drivers_forms
from app.pubsub import DeviceTokensNotifier
from app.pubsub.drivers import DriverActivator
from app.pubsub.drivers import DriverCreator
from app.pubsub.drivers import DriverDeactivator
from app.pubsub.drivers import DriverUpdater
from app.pubsub.drivers import DriverSerializer
from app.pubsub.drivers import DriverWithIdGetter
from app.pubsub.drivers import DriversDeviceTokenExtractor
from app.pubsub.drivers import UnhiddenDriversGetter
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class AddDriverWorkflow(Publisher):
    """Defines a workflow to add a new driver."""

    def perform(self, orm, logger, params, repository, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_creator = DriverCreator()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                driver_creator.perform(repository, user_id,
                                       form.d.license_plate, form.d.telephone)

        class DriverCreatorSubscriber(object):
            def driver_created(self, driver):
                orm.add(driver)
                outer.publish('success', driver.id)

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_creator.add_subscriber(logger, DriverCreatorSubscriber())
        form_validator.perform(drivers_forms.add(), params,
                               describe_invalid_form)


class ViewDriverWorkflow(Publisher):
    """Defines a workflow to view the details of a registered driver."""

    def perform(self, logger, repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = DriverWithIdGetter()
        driver_serializer = DriverSerializer()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                driver_serializer.perform(driver)

        class DriverSerializerSubscriber(object):
            def driver_serialized(self, blob):
                outer.publish('success', blob)


        drivers_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_serializer.add_subscriber(logger,
                                         DriverSerializerSubscriber())
        drivers_getter.perform(repository, driver_id)


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
            def valid_form(self, form):
                driver_updater.perform(repository, driver_id,
                                       form.d.license_plate,
                                       form.d.telephone)

        class DriverUpdaterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_updated(self, driver):
                orm.add(driver)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_updater.add_subscriber(logger, DriverUpdaterSubscriber())
        form_validator.perform(drivers_forms.update(), params,
                               describe_invalid_form)


class HideDriverWorkflow(Publisher):
    """Defines a workflow to _temporarily_ hide a driver."""

    def perform(self, orm, logger, repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_deactivator = DriverDeactivator()

        class DriverDeactivatorSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_hid(self, driver):
                orm.add(driver)
                outer.publish('success')

        driver_deactivator.add_subscriber(logger, DriverDeactivatorSubscriber())
        driver_deactivator.perform(repository, driver_id)


class UnhideDriverWorkflow(Publisher):
    """Defines a workflow to unhide a driver."""

    def perform(self, orm, logger, repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_activator = DriverActivator()

        class DriverActivatorSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_unhid(self, driver):
                orm.add(driver)
                outer.publish('success')

        driver_activator.add_subscriber(logger, DriverActivatorSubscriber())
        driver_activator.perform(repository, driver_id)


class NotifyDriversWorkflow(Publisher):
    """Defines a workflow to notify all the drivers that a new passenger is
    looking for a passage.
    """

    def perform(self, logger, repository, push_adapter, channel, payload):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = UnhiddenDriversGetter()
        device_token_extractor = DriversDeviceTokenExtractor()
        device_notifier = DeviceTokensNotifier()

        class DriversGetterSubscriber(object):
            def unhidden_drivers_found(self, drivers):
                device_token_extractor.perform(drivers)

        class DeviceTokensExtractorSubscriber(object):
            def device_tokens_extracted(self, device_tokens):
                device_notifier.perform(push_adapter, channel, device_tokens,
                                        payload)

        class DeviceNotifierSubscriber(object):
            def device_tokens_not_notified(self, error):
                outer.publish('failure', error)
            def device_tokens_notified(self):
                outer.publish('success')

        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        device_token_extractor.add_subscriber(logger,
                                              DeviceTokensExtractorSubscriber())
        device_notifier.add_subscriber(logger, DeviceNotifierSubscriber())
        drivers_getter.perform(repository)
