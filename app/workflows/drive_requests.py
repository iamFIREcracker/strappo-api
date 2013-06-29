#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.pubsub.passengers import PassengerDeactivator
from app.pubsub.drive_requests import DriveRequestCreator
from app.pubsub.drive_requests import DriveRequestAcceptor
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import TaskSubmitter


class AddDriveRequestWorkflow(Publisher):
    """Defines a workflow to create a new ride request."""

    def perform(self, orm, logger, repository, driver_id, passenger_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        request_creator = DriveRequestCreator()
        task_submitter = TaskSubmitter()

        class DriveRequestCreatorSubscriber(object):
            def drive_request_created(self, request):
                orm.add(request)
                task_submitter.perform(task, request.passenger_id)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        request_creator.add_subscriber(logger, DriveRequestCreatorSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        request_creator.perform(repository, driver_id, passenger_id)


class AcceptDriveRequestWorkflow(Publisher):
    """Defines a workflow to mark a drive request as accepted."""

    def perform(self, orm, logger, drive_requests_repository,
                driver_id, passenger_id, passengers_repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        request_acceptor = DriveRequestAcceptor()
        passenger_deactivator = PassengerDeactivator()

        class DriveRequestAcceptorSubscriber(object):
            def drive_request_not_found(self, driver_id, passenger_id):
                outer.publish('not_found')
            def drive_request_accepted(self, request):
                orm.add(request)
                passenger_deactivator.perform(passengers_repository,
                                              request.passenger_id)

        class PassengerDeactivatorRequestSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found')
            def passenger_hid(self, passenger):
                orm.add(passenger)
                outer.publish('success')

        request_acceptor.add_subscriber(logger, DriveRequestAcceptorSubscriber())
        passenger_deactivator.\
                add_subscriber(logger, PassengerDeactivatorRequestSubscriber())
        request_acceptor.perform(drive_requests_repository, driver_id,
                                 passenger_id)