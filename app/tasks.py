#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import web

from app.celery import celery
from app.pubsub.notifications import notificationid_for_user
from app.repositories.drive_requests import DriveRequestsRepository
from app.repositories.drivers import DriversRepository
from app.repositories.passengers import PassengersRepository
from app.weblib.adapters.push.titanium import TitaniumPushNotificationsAdapter
from app.weblib.db import create_session
from app.weblib.gettext import create_gettext
from app.weblib.logging import create_logger
from app.weblib.redis import create_redis
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.workflows.drive_requests import DeactivateActiveDriveRequestsWorkflow
from app.workflows.drivers import NotifyDriverWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import NotifyAllDriversWorkflow
from app.workflows.drivers import UnhideHiddenDriversWorkflow
from app.workflows.passengers import DeactivateActivePassengersWorkflow
from app.workflows.passengers import NotifyPassengersWorkflow


@celery.task
def NotifyDriverDriveRequestAccepted(request):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_driver = NotifyDriverWorkflow()
    ret = Future()
    alert = gettext('alert_matched_passenger',
                    lang=request['driver']['user']['locale']) % \
            dict(name=request['passenger']['user']['name'])
    badge = redis.\
            incr(notificationid_for_user(request['passenger']['user']['id']))

    class NotifyDriverSubscriber(object):
        def driver_not_found(self, driver_id):
            ret.set((None, 'Driver not found: %(driver_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_driver.add_subscriber(logging_subscriber,
                                 NotifyDriverSubscriber())
    notify_driver.perform(logger, DriversRepository, request['driver']['id'],
                          push_adapter, channel,
                          json.dumps({
                              'badge': badge,
                              'channel': channel,
                              'kind': 'matched_passenger',
                              'drive_request': request['id'],
                              'sound': 'default',
                              'icon': 'notificationicon',
                              'alert': alert
                          }))
    return ret.get()


@celery.task
def NotifyDriverDriveRequestCancelledByPassengerTask(request):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_driver = NotifyDriverWorkflow()
    ret = Future()
    alert = gettext('alert_cancelled_drive_request_by_passenger',
                    lang=request['driver']['user']['locale']) % \
            dict(name=request['passenger']['user']['name'])
    badge = redis.\
            incr(notificationid_for_user(request['driver']['user']['id']))

    class NotifyDriverSubscriber(object):
        def driver_not_found(self, driver_id):
            ret.set((None, 'Driver not found: %(driver_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_driver.add_subscriber(logging_subscriber,
                                 NotifyDriverSubscriber())
    notify_driver.perform(logger, DriversRepository, request['driver']['id'],
                          push_adapter, channel,
                          json.dumps({
                              'badge': badge,
                              'channel': channel,
                              'kind': 'cancelled_drive_request',
                              'passenger': request['passenger']['id'],
                              'sound': 'default',
                              'icon': 'notificationicon',
                              'alert': alert
                          }))
    return ret.get()


@celery.task
def NotifyDriversPassengerRegisteredTask(passenger):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_drivers = NotifyAllDriversWorkflow()
    ret = Future()

    def payload_factory(user):
        alert = gettext('alert_unmatched_passenger', lang=user.locale) % \
                dict(name=passenger['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'kind': 'unmatched_passenger',
            'passenger': passenger['id'],
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyDriversSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_drivers.add_subscriber(logging_subscriber,
                                  NotifyDriversSubscriber())
    notify_drivers.perform(logger, DriversRepository, push_adapter, channel,
                           payload_factory)
    return ret.get()


@celery.task
def NotifyDriversPassengerAlitTask(requests):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_drivers = NotifyDriversWorkflow()
    ret = Future()

    def payload_factory(user):
        # If we are invoked it means there is at least one passenger
        # in the list of requests, so the following operation should
        # be safe!
        alert = gettext('alert_alit_passenger', lang=user.locale) % \
                dict(name=requests[0]['passenger']['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'kind': 'alighted_passenger',
            'passenger': requests[0]['passenger']['id'],
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyDriversSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_drivers.add_subscriber(logging_subscriber,
                                  NotifyDriversSubscriber())
    notify_drivers.perform(logger, DriversRepository,
                           [r['driver']['id'] for r in requests],
                           push_adapter, channel, payload_factory)
    return ret.get()


@celery.task
def NotifyDriversDeactivatedPassengerTask(requests):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_drivers = NotifyDriversWorkflow()
    ret = Future()

    def payload_factory(user):
        # If we are invoked it means there is at least one passenger
        # in the list of requests, so the following operation should
        # be safe!
        alert = gettext('alert_deactivated_passenger', lang=user.locale) % \
                dict(name=requests[0]['passenger']['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'kind': 'deactivated_passenger',
            'passenger': requests[0]['passenger']['id'],
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyDriversSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_drivers.add_subscriber(logging_subscriber,
                                  NotifyDriversSubscriber())
    notify_drivers.perform(logger, DriversRepository,
                           [r['driver']['id'] for r in requests],
                           push_adapter, channel, payload_factory)
    return ret.get()


@celery.task
def NotifyPassengerDriveRequestPending(request):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    def payload_factory(user):
        alert = gettext('alert_pending_drive_request', lang=user.locale) % \
            dict(name=request['driver']['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'kind': 'pending_drive_request',
            'drive_request': request['id'],
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyPassengerSubscriber(object):
        def passenger_not_found(self, passenger_id):
            ret.set((None, 'Passenger not found: %(passenger_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                    NotifyPassengerSubscriber())
    notify_passengers.perform(logger, PassengersRepository,
                              [request['passenger']['id']],
                              push_adapter, channel, payload_factory)
    return ret.get()


@celery.task
def NotifyPassengersDriverDeactivatedTask(requests):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    def payload_factory(user):
        # If we are invoked it means there is at least one passenger
        # in the list of requests, so the following operation should
        # be safe!
        alert = gettext('alert_deactivated_driver', lang=user.locale) % \
                dict(name=requests[0]['driver']['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyPassengersSubscriber(object):
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                     NotifyPassengersSubscriber())
    notify_passengers.perform(logger, PassengersRepository,
                              [r['passenger']['id'] for r in requests],
                              push_adapter, channel, payload_factory)
    return ret.get()



@celery.task
def NotifyPassengerDriveRequestCancelledTask(request):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    def payload_factory(user):
        alert = gettext('alert_cancelled_drive_request_by_driver',
                        lang=user.locale) % \
                dict(name=request['driver']['user']['name'])
        badge = redis.\
                incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'kind': 'cancelled_drive_request',
            'driver': request['driver']['id'],
            'sound': 'default',
            'icon': 'notificationicon',
            'alert': alert
        })

    class NotifyPassengerSubscriber(object):
        def passenger_not_found(self, passenger_id):
            ret.set((None, 'Passenger not found: %(passenger_id)s' % locals()))
        def failure(self, error):
            ret.set((None, error))
        def success(self):
            ret.set((None, None))

    notify_passengers.add_subscriber(logging_subscriber,
                                    NotifyPassengerSubscriber())
    notify_passengers.perform(logger, PassengersRepository,
                              [request['passenger']['id']], push_adapter,
                              channel, payload_factory)
    return ret.get()


#@celery.task
#def DeactivateActivePassengers():
#    logger = create_logger()
#    orm = create_session()
#    logging_subscriber = LoggingSubscriber(logger)
#    deactivate_passengers = DeactivateActivePassengersWorkflow()
#    ret = Future()
#
#    class DeactivatePassengersSubscriber(object):
#        def success(self, passengers):
#            orm.commit()
#            ret.set(passengers)
#
#    deactivate_passengers.add_subscriber(logging_subscriber,
#                                         DeactivatePassengersSubscriber())
#    deactivate_passengers.perform(logger, orm, PassengersRepository)
#    return ret.get()
#
#
#@celery.task
#def DeactivateActiveDriveRequests():
#    logger = create_logger()
#    orm = create_session()
#    logging_subscriber = LoggingSubscriber(logger)
#    deactivate_drive_requests = DeactivateActiveDriveRequestsWorkflow()
#    ret = Future()
#
#    class DeactivateDriveRequestsSubscriber(object):
#        def success(self, drive_requests):
#            orm.commit()
#            ret.set(drive_requests)
#
#    deactivate_drive_requests.add_subscriber(logging_subscriber,
#                                             DeactivateDriveRequestsSubscriber())
#    deactivate_drive_requests.perform(logger, orm, DriveRequestsRepository)
#    return ret.get()
#
#
#@celery.task
#def UnhideHiddenDrivers():
#    logger = create_logger()
#    orm = create_session()
#    logging_subscriber = LoggingSubscriber(logger)
#    unhide_drivers = UnhideHiddenDriversWorkflow()
#    ret = Future()
#
#    class UnhideDriversSubscriber(object):
#        def success(self, drivers):
#            orm.commit()
#            ret.set(drivers)
#
#    unhide_drivers.add_subscriber(logger, UnhideDriversSubscriber())
#    unhide_drivers.perform(logger, orm, DriversRepository)
