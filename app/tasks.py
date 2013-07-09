#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.celery import celery

from app.repositories.drive_requests import DriveRequestsRepository
from app.repositories.drivers import DriversRepository
from app.repositories.passengers import PassengersRepository
from app.weblib.adapters.push.titanium import TitaniumPushNotificationsAdapter
from app.weblib.db import create_session
from app.weblib.logging import create_logger
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.workflows.drive_requests import DeactivateActiveDriveRequestsWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import UnhideHiddenDriversWorkflow
from app.workflows.passengers import DeactivateActivePassengersWorkflow
from app.workflows.passengers import NotifyPassengerWorkflow


@celery.task
def NotifyDriversTask(passenger_id):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_drivers = NotifyDriversWorkflow()
    ret = Future()

    class NotifyDriversSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_drivers.add_subscriber(logging_subscriber,
                                    NotifyDriversSubscriber())
    notify_drivers.perform(logger, DriversRepository, push_adapter, 'drivers',
                           'A new passenger is waiting for you!') # XXX TBD payload
    return ret.get()


@celery.task
def NotifyPassengerTask(passenger_id):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passenger = NotifyPassengerWorkflow()
    ret = Future()

    class NotifyPassengerSubscriber(object):
        def passenger_not_found(self, passenger_id):
            ret.set((None, 'Passenger not found: %(passenger_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passenger.add_subscriber(logging_subscriber,
                                    NotifyPassengerSubscriber())
    notify_passenger.perform(logger, PassengersRepository, passenger_id,
                             push_adapter, 'passengers',
                             'A driver has offered to give you a ride') # XXX TBD payload
    return ret.get()


@celery.task
def DeactivateActivePassengers():
    logger = create_logger()
    orm = create_session()
    logging_subscriber = LoggingSubscriber(logger)
    deactivate_passengers = DeactivateActivePassengersWorkflow()
    ret = Future()

    class DeactivatePassengersSubscriber(object):
        def success(self, passengers):
            orm.commit()
            ret.set(passengers)

    deactivate_passengers.add_subscriber(logging_subscriber,
                                         DeactivatePassengersSubscriber())
    deactivate_passengers.perform(logger, orm, PassengersRepository)
    return ret.get()


@celery.task
def DeactivateActiveDriveRequests():
    logger = create_logger()
    orm = create_session()
    logging_subscriber = LoggingSubscriber(logger)
    deactivate_drive_requests = DeactivateActiveDriveRequestsWorkflow()
    ret = Future()

    class DeactivateDriveRequestsSubscriber(object):
        def success(self, drive_requests):
            orm.commit()
            ret.set(drive_requests)

    deactivate_drive_requests.add_subscriber(logging_subscriber,
                                             DeactivateDriveRequestsSubscriber())
    deactivate_drive_requests.perform(logger, orm, DriveRequestsRepository)
    return ret.get()


@celery.task
def UnhideHiddenDrivers():
    logger = create_logger()
    orm = create_session()
    logging_subscriber = LoggingSubscriber(logger)
    unhide_drivers = UnhideHiddenDriversWorkflow()
    ret = Future()

    class UnhideDriversSubscriber(object):
        def success(self, drivers):
            orm.commit()
            ret.set(drivers)

    unhide_drivers.add_subscriber(logger, UnhideDriversSubscriber())
    unhide_drivers.perform(logger, orm, DriversRepository)
