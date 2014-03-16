#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

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
from app.workflows.drivers import NotifyDriverWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import UnhideHiddenDriversWorkflow
from app.workflows.passengers import DeactivateActivePassengersWorkflow
from app.workflows.passengers import NotifyPassengersWorkflow


@celery.task
def NotifyDriverDriveRequestAccepted(passenger_name, driver_id):
    return notify_driver(driver_id,
                         '%(name)s just accepted your drive request!' \
                         % dict(name=passenger_name))


@celery.task
def NotifyDriverDriveRequestCancelledByPassengerTask(passenger_name,
                                                     driver_id):
    return notify_driver(driver_id,
                         '%(name)s just cancelled her drive request!' \
                         % dict(name=passenger_name))


def notify_driver(driver_id, message):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_driver = NotifyDriverWorkflow()
    ret = Future()

    class NotifyDriverSubscriber(object):
        def driver_not_found(self, driver_id):
            ret.set((None, 'Driver not found: %(driver_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_driver.add_subscriber(logging_subscriber,
                                    NotifyDriverSubscriber())
    notify_driver.perform(logger, DriversRepository, driver_id,
                              push_adapter, 'channel',
                              json.dumps({
                                  'channel': 'channel',
                                  'alert': message
                              }))
    return ret.get()


@celery.task
def NotifyDriversTask(passenger_name):
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
                           json.dumps({
                               'channel': 'channel',
                               'alert': 'Hei, %(name)s is looking '
                                        'for a lift!' \
                                                % dict(name=passenger_name)
                           }))
    return ret.get()


@celery.task
def NotifyDriversAlitPassengerTask(passenger_name, driver_ids):
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
                           json.dumps({
                               'channel': 'channel',
                               'alert': '%(name)s is so thankful '
                                        'for the ride!' \
                                                % dict(name=passenger_name)
                           }))
    return ret.get()


@celery.task
def NotifyDriversDeactivatedPassengerTask(passenger_name, driver_ids):
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
    notify_drivers.perform(logger, DriversRepository, push_adapter, 'channel',
                           json.dumps({
                               'channel': 'channel',
                               'alert': 'Oh no, %(name)s is no more '
                                        'looking for a ride!' \
                                                % dict(name=passenger_name)
                           }))
    return ret.get()


@celery.task
def NotifyPassengerDriveRequestPending(driver_name, passenger_id):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    class NotifyPassengerSubscriber(object):
        def passenger_not_found(self, passenger_id):
            ret.set((None, 'Passenger not found: %(passenger_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                    NotifyPassengerSubscriber())
    notify_passengers.perform(logger, PassengersRepository, [passenger_id],
                              push_adapter, 'channel',
                              json.dumps({
                                  'channel': 'channel',
                                  'alert': 'Yeah, %(name)s has offered '
                                           'to give you a ride!' \
                                                   % dict(name=driver_name)
                              }))
    return ret.get()


@celery.task
def NotifyPassengersDriverDeactivatedTask(driver_name, passenger_ids):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    class NotifyPassengersSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                     NotifyPassengersSubscriber())
    notify_passengers.perform(logger, PassengersRepository, passenger_ids,
                              push_adapter, 'channel',
                              json.dumps({
                                  'channel': 'channel',
                                  'alert': 'Oh no, %(name)s cannot drive '
                                           'you around anymore!' \
                                                   % dict(name=driver_name)
                              }))
    return ret.get()



@celery.task
def NotifyPassengerDriveRequestCancelledTask(driver_name, passenger_id):
    logger = create_logger()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    class NotifyPassengerSubscriber(object):
        def passenger_not_found(self, passenger_id):
            ret.set((None, 'Passenger not found: %(passenger_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                    NotifyPassengerSubscriber())
    notify_passengers.perform(logger, PassengersRepository, [passenger_id],
                              push_adapter, 'passengers',
                              json.dumps({
                                  'channel': 'channel',
                                  'alert': 'Oh noes, %(name)s just cancelled '
                                           'her drive request!' \
                                                   % dict(name=driver_name)
                              }))
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
