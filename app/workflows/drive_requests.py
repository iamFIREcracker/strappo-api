#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.drive_requests import ActiveDriveRequestsFilterExtractor
from app.pubsub.drive_requests import ActiveDriveRequestsGetter
from app.pubsub.drive_requests import ActiveDriveRequestsWithDriverIdGetter
from app.pubsub.drive_requests import ActiveDriveRequestsWithPassengerIdGetter
from app.pubsub.drive_requests import DriveRequestAcceptor
from app.pubsub.drive_requests import DriveRequestCancellorByDriverId
from app.pubsub.drive_requests import DriveRequestCancellorByPassengerId
from app.pubsub.drive_requests import DriveRequestCreator
from app.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from app.pubsub.drive_requests import MultipleDriveRequestsSerializer
from app.pubsub.drivers import DeepDriverWithIdGetter
from app.pubsub.drivers import DriverWithIdGetter
from app.pubsub.drivers import DriverWithUserIdAuthorizer
from app.pubsub.drivers import DriverWithoutDriveRequestForPassengerValidator
from app.pubsub.passengers import MultiplePassengerMatcher
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import PassengerWithUserIdAuthorizer
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import TaskSubmitter


class ListActiveDriveRequestsWorkflow(Publisher):
    """Defines a workflow to list all the active drive requests associated
    with a specific driver ID."""

    def perform(self, logger, drivers_repository, passengers_repository,
                requests_repository, user_id, params):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        filter_extractor = ActiveDriveRequestsFilterExtractor()
        with_driver_id_requests_getter = ActiveDriveRequestsWithDriverIdGetter()
        driver_getter = DriverWithIdGetter()
        driver_authorizer = DriverWithUserIdAuthorizer()
        with_passenger_id_requests_getter = \
                ActiveDriveRequestsWithPassengerIdGetter()
        passenger_getter = PassengerWithIdGetter()
        passenger_authorizer = PassengerWithUserIdAuthorizer()
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
                with_driver_id_requests_getter.perform(requests_repository,
                                                       driver.id)

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

        class ActiveDriveRequestsGetterSubscriber(object):
            def drive_requests_found(self, requests):
                requests_serializer.perform(requests)

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, blob):
                outer.publish('success', blob)

        filter_extractor.add_subscriber(logger, FilterExtractorSubscriber())
        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        driver_authorizer.add_subscriber(logger, DriverAuthorizerSubscriber())
        with_driver_id_requests_getter.\
                add_subscriber(logger, ActiveDriveRequestsGetterSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        passenger_authorizer.add_subscriber(logger,
                                            PassengerAuthorizerSubscriber())
        with_passenger_id_requests_getter.\
                add_subscriber(logger, ActiveDriveRequestsGetterSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        filter_extractor.perform(params)


class AddDriveRequestWorkflow(Publisher):
    """Defines a workflow to create a new ride request."""

    def perform(self, orm, logger, user_id, drivers_repository, driver_id,
                passengers_repository, passenger_id, requests_repository,
                task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DeepDriverWithIdGetter()
        passenger_getter = PassengerWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        driver_validator = DriverWithoutDriveRequestForPassengerValidator()
        request_creator = DriveRequestCreator()
        request_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        driver_future = Future()
        passenger_future = Future()

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
                request_creator.perform(requests_repository, driver_id,
                                        passenger_id)

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

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        driver_validator.add_subscriber(logger, DriverValidatorSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        request_creator.add_subscriber(logger, DriveRequestCreatorSubscriber())
        request_serializer.add_subscriber(logger,
                                          DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        driver_getter.perform(drivers_repository, driver_id)


class CancelDriveOfferWorkflow(Publisher):
    """Defines a workflow to cancel an existing ride request."""

    def perform(self, orm, logger, drivers_repository, user_id, driver_id,
                requests_repository, drive_request_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        request_cancellor = DriveRequestCancellorByDriverId()
        task_submitter = TaskSubmitter()
        driver_future = Future()

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
                request_cancellor.perform(requests_repository,
                                          drive_request_id, driver_id)

        class DriveRequestCancellorSubscriber(object):
            def drive_request_not_found(self, drive_request_id, driver_id):
                outer.publish('success')

            def drive_request_cancelled(self, request):
                orm.add(request)
                task_submitter.perform(task, driver_future.get().user.name,
                                       request.passenger_id)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_cancellor.add_subscriber(logger,
                                         DriveRequestCancellorSubscriber())
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
                task_submitter.perform(task, passenger_future.get().user.name,
                                       request.driver_id)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_cancellor.add_subscriber(logger,
                                         DriveRequestCancellorSubscriber())
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


class DeactivateActiveDriveRequestsWorkflow(Publisher):
    """Defines a workflow to mark all active drive requests as hidden"""

    def perform(self, logger, orm, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        requests_getter = ActiveDriveRequestsGetter()
        requests_deactivator = MultipleDriveRequestsDeactivator()

        class DriveRequestsGetterSubscriber(object):
            def drive_requests_found(self, requests):
                requests_deactivator.perform(requests)

        class DriveRequestsDeactivatorSubscriber(object):
            def drive_requests_hid(self, requests):
                orm.add_all(requests)
                outer.publish('success', requests)

        requests_getter.add_subscriber(logger, DriveRequestsGetterSubscriber())
        requests_deactivator.add_subscriber(logger,
                                            DriveRequestsDeactivatorSubscriber())
        requests_getter.perform(repository)
