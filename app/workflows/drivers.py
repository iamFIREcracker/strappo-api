#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.drivers as drivers_forms
from app.pubsub import ACSUserIdsNotifier
from app.pubsub.drivers import DriverCreator
from app.pubsub.drivers import DriverHider
from app.pubsub.drivers import DriverUpdater
from app.pubsub.drivers import DriverSerializer
from app.pubsub.drivers import DriverWithIdGetter
from app.pubsub.drivers import DriversACSUserIdExtractor
from app.pubsub.drivers import DriverWithUserIdAuthorizer
from app.pubsub.drivers import HiddenDriversGetter
from app.pubsub.drivers import MultipleDriversUnhider
from app.pubsub.drivers import UnhiddenDriversGetter
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Future
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

    def perform(self, orm, logger, params, repository, driver_id, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        driver_updater = DriverUpdater()
        future_form = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                future_form.set(form)
                driver_getter.perform(repository, driver_id)

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                authorizer.perform(user_id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                form = future_form.get()
                driver_updater.perform(driver, form.d.license_plate,
                                       form.d.telephone)

        class DriverUpdaterSubscriber(object):
            def driver_updated(self, driver):
                orm.add(driver)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        driver_updater.add_subscriber(logger, DriverUpdaterSubscriber())
        form_validator.perform(drivers_forms.update(), params,
                               describe_invalid_form)


class HideDriverWorkflow(Publisher):
    """Defines a workflow to _temporarily_ hide a driver."""

    def perform(self, orm, logger, repository, driver_id, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        driver_hider = DriverHider()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                authorizer.perform(user_id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                driver_hider.perform(driver)

        class DriverHiderSubscriber(object):
            def driver_hid(self, driver):
                orm.add(driver)
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        driver_hider.add_subscriber(logger, DriverHiderSubscriber())
        driver_getter.perform(repository, driver_id)


class UnhideDriverWorkflow(Publisher):
    """Defines a workflow to unhide a driver."""

    def perform(self, orm, logger, repository, driver_id, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        drivers_unhider = MultipleDriversUnhider()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                authorizer.perform(user_id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                drivers_unhider.perform([driver])

        class DriversUnhiderSubscriber(object):
            def drivers_unhid(self, drivers):
                orm.add(drivers[0])
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        drivers_unhider.add_subscriber(logger, DriversUnhiderSubscriber())
        driver_getter.perform(repository, driver_id)


class NotifyDriversWorkflow(Publisher):
    """Defines a workflow to notify all the drivers that a new passenger is
    looking for a passage.
    """

    def perform(self, logger, repository, push_adapter, channel, payload):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = UnhiddenDriversGetter()
        acs_ids_extractor = DriversACSUserIdExtractor()
        acs_notifier = ACSUserIdsNotifier()

        class DriversGetterSubscriber(object):
            def unhidden_drivers_found(self, drivers):
                acs_ids_extractor.perform(drivers)

        class ACSUserIdsExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                acs_notifier.perform(push_adapter, channel, user_ids, payload)

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)
            def acs_user_ids_notified(self):
                outer.publish('success')

        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        drivers_getter.perform(repository)


class UnhideHiddenDriversWorkflow(Publisher):
    """Defines a workflow to unhide all the previously hidden drivers."""

    def perform(self, logger, orm, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = HiddenDriversGetter()
        drivers_unhider = MultipleDriversUnhider()

        class DriversGetterSubscriber(object):
            def hidden_drivers_found(self, drivers):
                drivers_unhider.perform(drivers)

        class DriversUnhiderSubscriber(object):
            def drivers_unhid(self, drivers):
                orm.add_all(drivers)
                outer.publish('success', drivers)

        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        drivers_unhider.add_subscriber(logger, DriversUnhiderSubscriber())
        drivers_getter.perform(repository)
