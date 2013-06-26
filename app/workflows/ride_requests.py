#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.passengers import PassengerDeactivator
from app.pubsub.ride_requests import RideRequestCreator
from app.pubsub.ride_requests import RideRequestAcceptor
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import TaskSubmitter


class AddRideRequestWorkflow(Publisher):
    """Defines a workflow to create a new ride request."""

    def perform(self, orm, logger, repository, driver_id, passenger_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        request_creator = RideRequestCreator()
        task_submitter = TaskSubmitter()

        class RideRequestCreatorSubscriber(object):
            def ride_request_created(self, request):
                orm.add(request)
                task_submitter.perform(task, request.passenger_id)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        request_creator.add_subscriber(logger, RideRequestCreatorSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        request_creator.perform(repository, driver_id, passenger_id)


class AcceptRideRequestWorkflow(Publisher):
    """Defines a workflow to mark a drive request as accepted."""

    def perform(self, orm, logger, ride_requests_repository,
                driver_id, passenger_id, passengers_repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        request_acceptor = RideRequestAcceptor()
        passenger_deactivator = PassengerDeactivator()

        class RideRequestAcceptorSubscriber(object):
            def ride_request_not_found(self, driver_id, passenger_id):
                outer.publish('not_found')
            def ride_request_accepted(self, request):
                orm.add(request)
                passenger_deactivator.perform(passengers_repository,
                                              request.passenger_id)

        class PassengerDeactivatorRequestSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found')
            def passenger_hid(self, passenger):
                orm.add(passenger)
                outer.publish('success')

        request_acceptor.add_subscriber(logger, RideRequestAcceptorSubscriber())
        passenger_deactivator.\
                add_subscriber(logger, PassengerDeactivatorRequestSubscriber())
        request_acceptor.perform(ride_requests_repository, driver_id,
                                 passenger_id)
