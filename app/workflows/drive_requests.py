#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.drive_requests import ActiveDriveRequestsFilterExtractor
from app.pubsub.drive_requests import ActiveDriveRequestsGetter
from app.pubsub.drive_requests import ActiveDriveRequestsWithDriverIdGetter
from app.pubsub.drive_requests import ActiveDriveRequestsWithPassengerIdGetter
from app.pubsub.drive_requests import DriveRequestAcceptor
from app.pubsub.drive_requests import DriveRequestCreator
from app.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from app.pubsub.drive_requests import MultipleDriveRequestsSerializer
from app.pubsub.drivers import DriverWithIdGetter
from app.pubsub.drivers import DriverWithUserIdAuthorizer
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import PassengerWithUserIdAuthorizer
from app.pubsub.passengers import MultiplePassengersDeactivator
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import TaskSubmitter


class ListActiveDriveRequestsWorkflow(Publisher):
    """Defines a workflow to list all the active drive requests associated
    with a specific driver ID."""

    def perform(self, logger, repository, params):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        filter_extractor = ActiveDriveRequestsFilterExtractor()
        with_driver_id_requests_getter = ActiveDriveRequestsWithDriverIdGetter()
        with_passenger_id_requests_getter = \
                ActiveDriveRequestsWithPassengerIdGetter()
        requests_serializer = MultipleDriveRequestsSerializer()

        class FilterExtractorSubscriber(object):
            def by_driver_id_filter(self, driver_id):
                with_driver_id_requests_getter.perform(repository, driver_id)
            def by_passenger_id_filter(self, passenger_id):
                with_passenger_id_requests_getter.perform(repository,
                                                          passenger_id)

        class ActiveDriveRequestsGetterSubscriber(object):
            def drive_requests_found(self, requests):
                requests_serializer.perform(requests)

        class DriveRequestsSerializerSubscriber(object):
            def drive_requests_serialized(self, blob):
                outer.publish('success', blob)

        filter_extractor.add_subscriber(logger, FilterExtractorSubscriber())
        with_driver_id_requests_getter.\
                add_subscriber(logger, ActiveDriveRequestsGetterSubscriber())
        with_passenger_id_requests_getter.\
                add_subscriber(logger, ActiveDriveRequestsGetterSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestsSerializerSubscriber())
        filter_extractor.perform(params)


class AddDriveRequestWorkflow(Publisher):
    """Defines a workflow to create a new ride request."""

    def perform(self, orm, logger, drivers_repository, user_id, driver_id,
                requests_repository, passenger_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        driver_getter = DriverWithIdGetter()
        authorizer = DriverWithUserIdAuthorizer()
        request_creator = DriveRequestCreator()
        task_submitter = TaskSubmitter()

        class DriverGetterSubscriber(object):
            def driver_not_found(self, driver_id):
                outer.publish('not_found', driver_id)
            def driver_found(self, driver):
                authorizer.perform(user_id, driver)

        class AuthorizerSubscriber(object):
            def unauthorized(self, user_id, driver):
                outer.publish('unauthorized')
            def authorized(self, user_id, driver):
                request_creator.perform(requests_repository, driver_id, passenger_id)

        class DriveRequestCreatorSubscriber(object):
            def drive_request_created(self, request):
                orm.add(request)
                task_submitter.perform(task, request.passenger_id)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        driver_getter.add_subscriber(logger, DriverGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_creator.add_subscriber(logger, DriveRequestCreatorSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        driver_getter.perform(drivers_repository, driver_id)


class AcceptDriveRequestWorkflow(Publisher):
    """Defines a workflow to mark a drive request as accepted."""

    def perform(self, orm, logger, passengers_repository, passenger_id, user_id, 
                requests_repository, driver_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = PassengerWithIdGetter()
        authorizer = PassengerWithUserIdAuthorizer()
        request_acceptor = DriveRequestAcceptor()
        passengers_deactivator = MultiplePassengersDeactivator()

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
                orm.add(request)
                passengers_deactivator.perform([request.passenger])

        class PassengersDeactivatorSubscriber(object):
            def passengers_hid(self, passengers):
                orm.add(passengers[0])
                outer.publish('success')

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        authorizer.add_subscriber(logger, AuthorizerSubscriber())
        request_acceptor.add_subscriber(logger,
                                        DriveRequestAcceptorSubscriber())
        passengers_deactivator.add_subscriber(logger,
                                              PassengersDeactivatorSubscriber())
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
