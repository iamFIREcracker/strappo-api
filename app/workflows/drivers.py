#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub import ACSSessionCreator
from strappon.pubsub import ACSUserIdsNotifier
from strappon.pubsub import ACSPayloadsForUserIdNotifier
from strappon.pubsub import PayloadsByUserCreator
from strappon.pubsub.drive_requests import UnratedDriveRequestWithIdGetter
from strappon.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from strappon.pubsub.drive_requests import MultipleDriveRequestsSerializer
from strappon.pubsub.drivers import ActiveDriverWithIdGetter
from strappon.pubsub.drivers import DriverCreator
from strappon.pubsub.drivers import DriverWithIdGetter
from strappon.pubsub.drivers import DriversACSUserIdExtractor
from strappon.pubsub.drivers import DriverWithUserIdAuthorizer
from strappon.pubsub.drivers import MultipleDriversWithIdGetter
from strappon.pubsub.drivers import MultipleDriversDeactivator
from strappon.pubsub.drivers import UnhiddenDriversGetter
from strappon.pubsub.drivers import UnhiddenDriversByRegionGetter
from strappon.pubsub.notifications import NotificationsResetter
from strappon.pubsub.rates import RateCreator
from strappon.pubsub.passengers import MultiplePassengersUnmatcher
from strappon.pubsub.users import SerializedUserRegionExtractor
from weblib.forms import describe_invalid_form_localized
from weblib.pubsub import FormValidator
from weblib.pubsub import Future
from weblib.pubsub import Publisher
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import TaskSubmitter

import app.forms.drivers as drivers_forms
import app.forms.rates as rates_forms


class AddDriverWorkflow(Publisher):
    """Defines a workflow to add a new driver."""

    def perform(self, gettext, orm, logger, redis, params, repository, user):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_creator = DriverCreator()
        notifications_resetter = NotificationsResetter()
        driver_id_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                driver_creator.perform(repository, user.id,
                                       form.d.car_make,
                                       form.d.car_model,
                                       form.d.car_color,
                                       form.d.license_plate,
                                       form.d.telephone)

        class DriverCreatorSubscriber(object):
            def driver_created(self, driver):
                orm.add(driver)
                driver_id_future.set(driver.id)
                notifications_resetter.perform(redis, user.id)

        class NotificationsResetterSubscriber(object):
            def notifications_reset(self, recordid):
                outer.publish('success', driver_id_future.get())

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_creator.add_subscriber(logger, DriverCreatorSubscriber())
        notifications_resetter.\
            add_subscriber(logger, NotificationsResetterSubscriber())
        form_validator.perform(drivers_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))


class DeactivateDriverWorkflow(Publisher):
    """Defines a workflow to deactivate a driver given its ID."""

    def perform(self, logger, orm, repository, driver_id, user, task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = ActiveDriverWithIdGetter()
        with_user_id_authorizer = DriverWithUserIdAuthorizer()
        drivers_deactivator = MultipleDriversDeactivator()
        requests_deactivator = MultipleDriveRequestsDeactivator()
        passengers_unmatcher = MultiplePassengersUnmatcher()
        requests_serializer = MultipleDriveRequestsSerializer()
        unmatchable_passengers_future = Future()
        notifiable_requests_future = Future()
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
                unmatchable_passengers_future.\
                    set([r.passenger for r in driver.drive_requests
                         if r.accepted])
                notifiable_requests_future.\
                    set([r for r in driver.drive_requests
                         if r.accepted or not r.passenger.matched])
                requests_deactivator.perform(driver.drive_requests)

        class DriveRequestsDeactivatorSubscriber(object):
            def drive_requests_hid(self, requests):
                orm.add_all(requests)
                passengers_unmatcher.\
                    perform(unmatchable_passengers_future.get())

        class PassengersUnmatcherSubscriber(object):
            def passengers_unmatched(self, passengers):
                orm.add_all(passengers)
                requests_serializer.perform(notifiable_requests_future.get())

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
        passengers_unmatcher.add_subscriber(logger,
                                            PassengersUnmatcherSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        driver_getter.perform(repository, driver_id)


class NotifyDriverWorkflow(Publisher):
    def perform(self, logger, repository, driver_id, push_adapter, channel,
                payload):
        outer = self  # Handy to access ``self`` from inner classes
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
        outer = self  # Handy to access ``self`` from inner classes
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
                payload_factory, serialized_user):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        region_extractor = SerializedUserRegionExtractor()
        drivers_getter = UnhiddenDriversGetter()
        drivers_by_region_getter = UnhiddenDriversByRegionGetter()
        payloads_creator = PayloadsByUserCreator()
        acs_ids_extractor = DriversACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSPayloadsForUserIdNotifier()
        drivers_future = Future()
        payloads_future = Future()
        user_ids_future = Future()

        class RegionExtractorSubscriber(object):
            def region_not_found(self):
                drivers_getter.perform(repository)

            def region_found(self, region):
                drivers_by_region_getter.perform(repository, region)

        class DriversGetterSubscriber(object):
            def unhidden_drivers_found(self, drivers):
                drivers_future.set(drivers)
                payloads_creator.perform(payload_factory,
                                         [d.user for d in drivers])

        class DriversByRegionGetterSubscriber(object):
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

        region_extractor.add_subscriber(logger, RegionExtractorSubscriber())
        drivers_getter.add_subscriber(logger, DriversGetterSubscriber())
        drivers_by_region_getter.\
            add_subscriber(logger, DriversByRegionGetterSubscriber())
        payloads_creator.add_subscriber(logger, PayloadsCreatorSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        region_extractor.perform(serialized_user)


class RateDriveRequestWorkflow(Publisher):
    def perform(self, logger, gettext, orm, user, params, driver_id,
                drive_request_id, drivers_repository,
                drive_requests_repository, rate_repository):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_getter = DriverWithIdGetter()
        with_user_id_authorizer = DriverWithUserIdAuthorizer()
        drive_request_getter = UnratedDriveRequestWithIdGetter()
        rate_creator = RateCreator()
        stars_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                v = int(form.d.stars) if form.d.stars else 3
                stars_future.set(v)
                driver_getter.perform(drivers_repository, driver_id)

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('driver_not_found', driver_id)

            def driver_found(self, driver):
                with_user_id_authorizer.perform(user.id, driver)

        class WithUserIdAuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')

            def authorized(self, user_id, driver):
                drive_request_getter.perform(drive_requests_repository,
                                             drive_request_id,
                                             driver_id,
                                             user.id)

        class DriveRequestGetterSubscriber(object):
            def drive_request_not_found(self, id):
                outer.publish('drive_request_not_found', id)

            def drive_request_found(self, request):
                rate_creator.perform(rate_repository,
                                     request.id,
                                     request.driver.user.id,
                                     request.passenger.user.id,
                                     True,
                                     stars_future.get())

        class RateCreatorSubscriber(object):
            def rate_created(self, rate):
                orm.add(rate)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        with_user_id_authorizer.\
            add_subscriber(logger, WithUserIdAuthorizerSubscriber())
        drive_request_getter.add_subscriber(logger,
                                            DriveRequestGetterSubscriber())
        rate_creator.add_subscriber(logger, RateCreatorSubscriber())
        form_validator.perform(rates_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))
