#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.drive_requests import ActiveDriveRequestsFilterExtractor
from strappon.pubsub.drive_requests import\
    ActiveDriveRequestsWithDriverIdGetter
from strappon.pubsub.drive_requests import\
    ActiveDriveRequestsWithPassengerIdGetter
from strappon.pubsub.drive_requests import\
    UnratedDriveRequestsWithDriverIdGetter
from strappon.pubsub.drive_requests import\
    UnratedDriveRequestsWithPassengerIdGetter
from strappon.pubsub.drive_requests import DriveRequestAcceptor
from strappon.pubsub.drive_requests import DriveRequestWithIdAndDriverIdGetter
from strappon.pubsub.drive_requests import DriveRequestCancellor
from strappon.pubsub.drive_requests import DriveRequestCancellorByPassengerId
from strappon.pubsub.drive_requests import DriveRequestCreator
from strappon.pubsub.drive_requests import DriveRequestsEnricher
from strappon.pubsub.drive_requests import DriverDriveRequestsEnricher
from strappon.pubsub.drive_requests import MultipleDriveRequestsSerializer
from strappon.pubsub.drivers import DeepDriverWithIdGetter
from strappon.pubsub.drivers import DriverWithIdGetter
from strappon.pubsub.drivers import DriverWithUserIdAuthorizer
from strappon.pubsub.drivers import\
    DriverWithoutDriveRequestForPassengerValidator
from strappon.pubsub.passengers import MultiplePassengerMatcher
from strappon.pubsub.passengers import PassengerUnmatcher
from strappon.pubsub.passengers import PassengerWithIdGetter
from strappon.pubsub.passengers import PassengerWithUserIdAuthorizer
from strappon.pubsub.perks import ActiveDriverPerksGetter
from weblib.forms import describe_invalid_form_localized
from weblib.pubsub import FormValidator
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher
from weblib.pubsub import TaskSubmitter
from app.forms import datetime_optional_parser

import app.forms.drive_requests as drive_requests_forms


class ListActiveDriverDriveRequestsWorkflow(Publisher):
    def perform(self, logger, drivers_repository,
                requests_repository, rates_repository, perks_repository,
                user_id, driver_id):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        with_driver_id_requests_getter = \
            ActiveDriveRequestsWithDriverIdGetter()
        driver_getter = DriverWithIdGetter()
        driver_authorizer = DriverWithUserIdAuthorizer()
        active_driver_perks_getter = ActiveDriverPerksGetter()
        driver_requests_enricher = DriverDriveRequestsEnricher()
        requests_serializer = MultipleDriveRequestsSerializer()
        requests_future = Future()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('unauthorized')

            def driver_found(self, driver):
                driver_authorizer.perform(user_id, driver)

        class DriverAuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')

            def authorized(self, user_id, driver):
                with_driver_id_requests_getter.perform(requests_repository,
                                                       driver.id)

        class ActiveDriveRequestsWithDriverIdGetterSubscriber(object):
            def drive_requests_found(self, requests):
                requests_future.set(requests)
                active_driver_perks_getter.perform(perks_repository,
                                                   user_id)

        class ActiveDriverPerksGetterSubscriber(object):
            def active_driver_perks_found(self, driver_perks):
                driver_requests_enricher.\
                    perform(rates_repository,
                            driver_perks[0].perk.fixed_rate,
                            driver_perks[0].perk.multiplier,
                            requests_future.get())

        class DriveRequestsEnricherSubscriber(object):
            def drive_requests_enriched(self, requests):
                requests_serializer.perform(requests)

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, blob):
                outer.publish('success', blob)

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_authorizer.add_subscriber(logger, DriverAuthorizerSubscriber())
        with_driver_id_requests_getter.\
            add_subscriber(
                logger, ActiveDriveRequestsWithDriverIdGetterSubscriber())
        active_driver_perks_getter.\
            add_subscriber(logger, ActiveDriverPerksGetterSubscriber())
        driver_requests_enricher.\
            add_subscriber(logger, DriveRequestsEnricherSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        driver_getter.perform(drivers_repository, driver_id)


class ListActivePassengerDriveRequestsWorkflow(Publisher):
    def perform(self, logger, passengers_repository,
                requests_repository, rates_repository, perks_repository,
                user_id, passenger_id):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        with_passenger_id_requests_getter = \
            ActiveDriveRequestsWithPassengerIdGetter()
        passenger_getter = PassengerWithIdGetter()
        passenger_authorizer = PassengerWithUserIdAuthorizer()
        passenger_requests_enricher = DriveRequestsEnricher()
        requests_serializer = MultipleDriveRequestsSerializer()
        requests_future = Future()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('unauthorized')

            def passenger_found(self, passenger):
                passenger_authorizer.perform(user_id, passenger)

        class PassengerAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')

            def authorized(self, user_id, passenger):
                with_passenger_id_requests_getter.perform(requests_repository,
                                                          passenger.id)

        class ActiveDriveRequestsWithPassengerIdGetterSubscriber(object):
            def drive_requests_found(self, requests):
                passenger_requests_enricher.perform(rates_repository, requests)

        class DriveRequestsEnricherSubscriber(object):
            def drive_requests_enriched(self, requests):
                requests_serializer.perform(requests)

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, blob):
                outer.publish('success', blob)

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        passenger_authorizer.add_subscriber(logger,
                                            PassengerAuthorizerSubscriber())
        with_passenger_id_requests_getter.\
            add_subscriber(
                logger, ActiveDriveRequestsWithPassengerIdGetterSubscriber())
        passenger_requests_enricher.\
            add_subscriber(logger, DriveRequestsEnricherSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        passenger_getter.perform(passengers_repository, passenger_id)


class ListUnratedDriveRequestsWorkflow(Publisher):
    """Defines a workflow to list all the active drive requests associated
    with a specific driver ID."""

    def perform(self, logger, drivers_repository, passengers_repository,
                requests_repository, rates_repository, user_id, params):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        filter_extractor = ActiveDriveRequestsFilterExtractor()
        driver_getter = DriverWithIdGetter()
        driver_authorizer = DriverWithUserIdAuthorizer()
        unrated_requests_with_driver_id_getter = \
                UnratedDriveRequestsWithDriverIdGetter()
        passenger_getter = PassengerWithIdGetter()
        passenger_authorizer = PassengerWithUserIdAuthorizer()
        unrated_requests_with_passenger_id_getter = \
                UnratedDriveRequestsWithPassengerIdGetter()
        requests_enricher = DriveRequestsEnricher()
        requests_serializer = MultipleDriveRequestsSerializer()

        class FilterExtractorSubscriber(object):
            def bad_request(self, params):
                outer.publish('bad_request')
            def by_driver_id_filter(self, driver_id):
                driver_getter.perform(drivers_repository, driver_id)
            def by_passenger_id_filter(self, passenger_id):
                passenger_getter.perform(passengers_repository, passenger_id)

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('unauthorized')
            def driver_found(self, driver):
                driver_authorizer.perform(user_id, driver)

        class DriverAuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                unrated_requests_with_driver_id_getter.\
                        perform(requests_repository, driver.id, driver.user.id)

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('unauthorized')
            def passenger_found(self, passenger):
                passenger_authorizer.perform(user_id, passenger)

        class PassengerAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')
            def authorized(self, user_id, passenger):
                unrated_requests_with_driver_id_getter.\
                        perform(requests_repository, passenger.id,
                                passenger.user.id)

        class UnratedDriveRequestsGetterSubscriber(object):
            def drive_requests_found(self, requests):
                requests_enricher.perform(rates_repository, requests)

        class DriveRequestsEnricherSubscriber(object):
            def drive_requests_enriched(self, requests):
                requests_serializer.perform(requests)

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, blob):
                outer.publish('success', blob)

        filter_extractor.add_subscriber(logger, FilterExtractorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_authorizer.add_subscriber(logger, DriverAuthorizerSubscriber())
        unrated_requests_with_driver_id_getter.\
                add_subscriber(logger, UnratedDriveRequestsGetterSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        passenger_authorizer.add_subscriber(logger,
                                            PassengerAuthorizerSubscriber())
        unrated_requests_with_passenger_id_getter.\
                add_subscriber(logger, UnratedDriveRequestsGetterSubscriber())
        requests_enricher.add_subscriber(logger,
                                         DriveRequestsEnricherSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        filter_extractor.perform(params)


class AddDriveRequestWorkflow(Publisher):
    """Defines a workflow to create a new ride request."""

    def perform(self, gettext, orm, logger, params, user,
                drivers_repository, driver_id, passengers_repository,
                passenger_id, requests_repository, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        driver_getter = DeepDriverWithIdGetter()
        passenger_getter = PassengerWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        driver_validator = DriverWithoutDriveRequestForPassengerValidator()
        request_creator = DriveRequestCreator()
        request_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        offered_pickup_time_future = Future()
        driver_future = Future()
        passenger_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                offered_pickup_time_future.\
                    set(datetime_optional_parser(form.d.offered_pickup_time))
                driver_getter.perform(drivers_repository, driver_id)

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                driver_future.set(driver)
                authorizer.perform(user.id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                driver_validator.perform(driver, passenger_id)

        class DriverValidatorSubscriber(object):
            def invalid_driver(self, errors):
                outer.publish('success')
            def valid_driver(self, driver):
                passenger_getter.perform(passengers_repository, passenger_id)

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found', passenger_id)
            def passenger_found(self, passenger):
                passenger_future.set(passenger)
                offered_pickup_time = offered_pickup_time_future.get()
                request_creator.\
                    perform(requests_repository, driver_id,
                            passenger_id,
                            offered_pickup_time=offered_pickup_time)

        class DriveRequestCreatorSubscriber(object):
            def drive_request_created(self, request):
                orm.add(request)
                request.driver = driver_future.get()
                request.passenger = passenger_future.get()
                request_serializer.perform([request])

        class DriveRequestSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests[0])

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        driver_validator.add_subscriber(logger, DriverValidatorSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        request_creator.add_subscriber(logger, DriveRequestCreatorSubscriber())
        request_serializer.add_subscriber(logger,
                                          DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        form_validator.perform(drive_requests_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))


class CancelDriveOfferWorkflow(Publisher):
    """Defines a workflow to cancel an existing ride request."""

    def perform(self, orm, logger, drivers_repository, user_id, driver_id,
                requests_repository, drive_request_id, task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        request_getter = DriveRequestWithIdAndDriverIdGetter()
        request_cancellor = DriveRequestCancellor()
        passenger_unmatcher = PassengerUnmatcher()
        requests_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        notifiable_request_future = Future()
        driver_future = Future()
        request_future = Future()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)

            def driver_found(self, driver):
                driver_future.set(driver)
                authorizer.perform(user_id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')

            def authorized(self, user_id, driver):
                request_getter.perform(requests_repository,
                                       drive_request_id, driver_id)

        class DriveRequestGetterSubscriber(object):
            def drive_request_not_found(self, drive_request_id, driver_id):
                outer.publish('success')

            def drive_request_found(self, request):
                notifiable_request_future.\
                    set(request.accepted or not request.passenger.matched)
                request_cancellor.perform(request)

        class DriveRequestCancellorSubscriber(object):
            def drive_request_cancelled(self, request):
                orm.add(request)
                request_future.set(request)
                if not notifiable_request_future.get():
                    outer.publish('success')
                else:
                    passenger_unmatcher.perform(request.passenger)

        class PassengerUnmatcherSubscriber(object):
            def passenger_unmatched(self, passenger):
                orm.add(passenger)
                requests_serializer.perform([request_future.get()])

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests[0])

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_getter.add_subscriber(logger, DriveRequestGetterSubscriber())
        request_cancellor.add_subscriber(logger,
                                         DriveRequestCancellorSubscriber())
        passenger_unmatcher.add_subscriber(logger,
                                           PassengerUnmatcherSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        driver_getter.perform(drivers_repository, driver_id)


class CancelDriveRequestWorkflow(Publisher):
    """Defines a workflow to cancel an existing ride request."""

    def perform(self, orm, logger, passengers_repository, user_id, passenger_id,
                requests_repository, drive_request_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = PassengerWithIdGetter()
        authorizer = PassengerWithUserIdAuthorizer()
        request_cancellor = DriveRequestCancellorByPassengerId()
        requests_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        passenger_future = Future()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found', passenger_id)
            def passenger_found(self, passenger):
                passenger_future.set(passenger)
                authorizer.perform(user_id, passenger)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')
            def authorized(self, user_id, passenger):
                request_cancellor.perform(requests_repository,
                                          drive_request_id, passenger_id)

        class DriveRequestCancellorSubscriber(object):
            def drive_request_not_found(self, drive_request_id, passenger_id):
                outer.publish('success')

            def drive_request_cancelled(self, request):
                orm.add(request)
                requests_serializer.perform([request])

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests[0])

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_cancellor.add_subscriber(logger,
                                         DriveRequestCancellorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        passenger_getter.perform(passengers_repository, passenger_id)


class AcceptDriveRequestWorkflow(Publisher):
    """Defines a workflow to mark a drive request as accepted."""

    def perform(self, orm, logger, passengers_repository, passenger_id, user_id,
                requests_repository, driver_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = PassengerWithIdGetter()
        authorizer = PassengerWithUserIdAuthorizer()
        request_acceptor = DriveRequestAcceptor()
        passengers_matcher = MultiplePassengerMatcher()
        request_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        passenger_future = Future()
        request_future = Future()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found', passenger_id)
            def passenger_found(self, passenger):
                authorizer.perform(user_id, passenger)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')
            def authorized(self, user_id, passenger):
                request_acceptor.perform(requests_repository, driver_id,
                                         passenger_id)

        class DriveRequestAcceptorSubscriber(object):
            def drive_request_not_found(self, driver_id, passenger_id):
                outer.publish('not_found') # XXX Bad request?!
            def drive_request_accepted(self, request):
                request_future.set(request)
                orm.add(request)
                passengers_matcher.perform([request.passenger])

        class PassengersMatcherSubscriber(object):
            def passengers_matched(self, passengers):
                passenger_future.set(passengers[0])
                orm.add(passengers[0])
                request = request_future.get()
                request.passenger = passengers[0]
                request_serializer.perform([request])

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests[0])

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_acceptor.add_subscriber(logger,
                                        DriveRequestAcceptorSubscriber())
        passengers_matcher.add_subscriber(logger, PassengersMatcherSubscriber())
        request_serializer.add_subscriber(logger,
                                          DriveRequestsSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        passenger_getter.perform(passengers_repository, passenger_id)
