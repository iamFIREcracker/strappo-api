#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.drivers as drivers_forms
from app.pubsub import ACSSessionCreator
from app.pubsub import ACSUserIdsNotifier
from app.pubsub import ACSPayloadsForUserIdNotifier
from app.pubsub import PayloadsByUserCreator
from app.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from app.pubsub.drive_requests import MultipleDriveRequestsSerializer
from app.pubsub.drivers import DriverCreator
from app.pubsub.drivers import DriverUpdater
from app.pubsub.drivers import DriverWithIdGetter
from app.pubsub.drivers import DriversACSUserIdExtractor
from app.pubsub.drivers import DriverWithUserIdAuthorizer
from app.pubsub.drivers import HiddenDriversGetter
from app.pubsub.drivers import MultipleDriversWithIdGetter
from app.pubsub.drivers import MultipleDriversDeactivator
from app.pubsub.drivers import MultipleDriversUnhider
from app.pubsub.drivers import UnhiddenDriversGetter
from app.pubsub.notifications import NotificationsResetter
from app.pubsub.users import UserWithoutDriverValidator
from app.weblib.forms import describe_invalid_form_localized
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Future
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import TaskSubmitter



class AddDriverWorkflow(Publisher):
    """Defines a workflow to add a new driver."""

    def perform(self, gettext, orm, logger, redis, params, repository, user):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_validator = UserWithoutDriverValidator()
        form_validator = FormValidator()
        driver_getter = DriverWithIdGetter()
        driver_creator = DriverCreator()
        driver_updater = DriverUpdater()
        notifications_resetter = NotificationsResetter()
        driver_future = Future()
        driver_id_future = Future()

        class UserValidatorSubscriber(object):
            def invalid_user(self, errors):
                driver_getter.perform(repository, user.driver.id)
            def valid_user(self, user):
                driver_future.set(None)
                form_validator.perform(drivers_forms.add(), params,
                                       describe_invalid_form_localized(gettext,
                                                                       user.locale))

        class DriverGetterSubscriber(object):
            def driver_found(self, driver):
                driver_future.set(driver)
                form_validator.perform(drivers_forms.add(), params,
                                       describe_invalid_form_localized(gettext,
                                                                       user.locale))

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                driver = driver_future.get()
                if driver is None:
                    driver_creator.perform(repository, user.id,
                                           form.d.license_plate,
                                           form.d.telephone)
                else:
                    driver_updater.perform(driver,
                                           form.d.license_plate,
                                           form.d.telephone)

        class DriverCreatorSubscriber(object):
            def driver_created(self, driver):
                orm.add(driver)
                driver_id_future.set(driver.id)
                notifications_resetter.perform(redis, user.id)

        class DriverUpdaterSubscriber(object):
            def driver_updated(self, driver):
                orm.add(driver)
                driver_id_future.set(driver.id)
                notifications_resetter.perform(redis, user.id)

        class NotificationsResetterSubscriber(object):
            def notifications_reset(self, recordid):
                outer.publish('success', driver_id_future.get())

        user_validator.add_subscriber(logger, UserValidatorSubscriber())
        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_creator.add_subscriber(logger, DriverCreatorSubscriber())
        driver_updater.add_subscriber(logger, DriverUpdaterSubscriber())
        notifications_resetter.\
                add_subscriber(logger, NotificationsResetterSubscriber())
        user_validator.perform(user)

class DeactivateDriverWorkflow(Publisher):
    """Defines a workflow to deactivate a driver given its ID."""

    def perform(self, logger, orm, repository, driver_id, user, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        with_user_id_authorizer = DriverWithUserIdAuthorizer()
        drivers_deactivator = MultipleDriversDeactivator()
        requests_deactivator = MultipleDriveRequestsDeactivator()
        requests_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('success')
            def driver_found(self, driver):
                with_user_id_authorizer.perform(user.id, driver)

        class WithUserIdAuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                drivers_deactivator.perform([driver])

        class DriversDeactivatorSubscriber(object):
            def drivers_hid(self, drivers):
                driver = orm.merge(drivers[0])
                orm.add(driver)
                requests_deactivator.perform(driver.drive_requests)

        class DriveRequestsDeactivatorSubscriber(object):
            def drive_requests_hid(self, requests):
                orm.add_all(requests)
                requests_serializer.perform(requests)

        class DriveRequestSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        with_user_id_authorizer.\
                add_subscriber(logger, WithUserIdAuthorizerSubscriber())
        drivers_deactivator.add_subscriber(logger,
                                              DriversDeactivatorSubscriber())
        requests_deactivator.\
                add_subscriber(logger, DriveRequestsDeactivatorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        driver_getter.perform(repository, driver_id)


class NotifyDriverWorkflow(Publisher):
    def perform(self, logger, repository, driver_id, push_adapter, channel,
                payload):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        acs_ids_extractor = DriversACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSUserIdsNotifier()
        user_ids_future = Future()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('driver_not_found', driver_id)
            def driver_found(self, driver):
                acs_ids_extractor.perform([driver])

        class ACSUserIdsExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                user_ids_future.set(user_ids)
                acs_session_creator.perform(push_adapter)

        class ACSSessionCreatorSubscriber(object):
            def acs_session_not_created(self, error):
                outer.publish('failure', error)
            def acs_session_created(self, session_id):
                acs_notifier.perform(push_adapter, session_id, channel,
                                     user_ids_future.get(), payload)

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)
            def acs_user_ids_notified(self):
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        driver_getter.perform(repository, driver_id)


class NotifyDriversWorkflow(Publisher):
    def perform(self, logger, repository, driver_ids, push_adapter, channel,
                payload_factory):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = MultipleDriversWithIdGetter()
        payloads_creator = PayloadsByUserCreator()
        acs_ids_extractor = DriversACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSPayloadsForUserIdNotifier()
        drivers_future = Future()
        payloads_future = Future()
        user_ids_future = Future()

        class DriversGetterSubscriber(object):
            def drivers_found(self, drivers):
                drivers_future.set(drivers)
                payloads_creator.perform(payload_factory,
                                         [d.user for d in drivers])

        class PayloadsCreatorSubscriber(object):
            def payloads_created(self, payloads):
                payloads_future.set(payloads)
                acs_ids_extractor.perform(drivers_future.get())

        class ACSUserIdsExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                user_ids_future.set(user_ids)
                acs_session_creator.perform(push_adapter)

        class ACSSessionCreatorSubscriber(object):
            def acs_session_not_created(self, error):
                outer.publish('failure', error)
            def acs_session_created(self, session_id):
                acs_notifier.perform(push_adapter, session_id, channel,
                                     zip(user_ids_future.get(),
                                         payloads_future.get()))

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)
            def acs_user_ids_notified(self):
                outer.publish('success')

        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        payloads_creator.add_subscriber(logger, PayloadsCreatorSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        drivers_getter.perform(repository, driver_ids)


class NotifyAllDriversWorkflow(Publisher):
    def perform(self, logger, repository, push_adapter, channel,
                payload_factory):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        drivers_getter = UnhiddenDriversGetter()
        payloads_creator = PayloadsByUserCreator()
        acs_ids_extractor = DriversACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSPayloadsForUserIdNotifier()
        drivers_future = Future()
        payloads_future = Future()
        user_ids_future = Future()

        class DriversGetterSubscriber(object):
            def unhidden_drivers_found(self, drivers):
                drivers_future.set(drivers)
                payloads_creator.perform(payload_factory,
                                         [d.user for d in drivers])

        class PayloadsCreatorSubscriber(object):
            def payloads_created(self, payloads):
                payloads_future.set(payloads)
                acs_ids_extractor.perform(drivers_future.get())

        class ACSUserIdsExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                user_ids_future.set(user_ids)
                acs_session_creator.perform(push_adapter)

        class ACSSessionCreatorSubscriber(object):
            def acs_session_not_created(self, error):
                outer.publish('failure', error)
            def acs_session_created(self, session_id):
                acs_notifier.perform(push_adapter, session_id, channel,
                                     zip(user_ids_future.get(),
                                         payloads_future.get()))

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)
            def acs_user_ids_notified(self):
                outer.publish('success')

        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        payloads_creator.add_subscriber(logger, PayloadsCreatorSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
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


