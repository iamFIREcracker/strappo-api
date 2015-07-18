#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import web

from strappon.pubsub.notifications import notificationid_for_user
from strappon.repositories.drivers import DriversRepository
from strappon.repositories.passengers import PassengersRepository
from strappon.repositories.users import UsersRepository
from weblib.adapters.push.titanium import TitaniumPushNotificationsAdapter
from weblib.db import create_session
from weblib.gettext import create_gettext
from weblib.logging import create_logger
from weblib.redis import create_redis
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber

from app.celery import celery
from app.workflows.drivers import NotifyDriverWorkflow
from app.workflows.drivers import NotifyDriversWorkflow
from app.workflows.drivers import NotifyAllDriversWorkflow
from app.workflows.passengers import NotifyPassengersWorkflow
from app.workflows.passengers import DeactivateExpiredPassengersWorkflow
from app.workflows.users import NotifyUserWorkflow


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
                              'slot': 'scoped',
                              'kind': 'matched_passenger',
                              'drive_request': request['id'],
                              'sound': 'default',
                              'vibrate': True,
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
                              'slot': 'scoped',
                              'kind': 'cancelled_drive_request',
                              'passenger': request['passenger']['id'],
                              'sound': 'default',
                              'vibrate': True,
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
            'slot': 'scoped',
            'kind': 'unmatched_passenger',
            'passenger': passenger['id'],
            'sound': 'default',
            'vibrate': True,
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
                           payload_factory, passenger['user'])
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
            'slot': 'scoped',
            'kind': 'alighted_passenger',
            'drive_request': requests[0]['id'],
            'sound': 'default',
            'vibrate': True,
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
            'slot': 'scoped',
            'kind': 'deactivated_passenger',
            'passenger': requests[0]['passenger']['id'],
            'sound': 'default',
            'vibrate': True,
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
            'slot': 'scoped',
            'kind': 'pending_drive_request',
            'drive_request': request['id'],
            'sound': 'default',
            'vibrate': True,
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
            'slot': 'scoped',
            'kind': 'deactivated_driver',
            'driver': requests[0]['driver']['id'],
            'sound': 'default',
            'vibrate': True,
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
            'slot': 'scoped',
            'kind': 'cancelled_drive_request',
            'driver': request['driver']['id'],
            'sound': 'default',
            'vibrate': True,
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


@celery.task
def NotifyPassengerDriverHonkedTask(passenger, driver):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_passengers = NotifyPassengersWorkflow()
    ret = Future()

    def payload_factory(user):
        alert = gettext('alert_honked_driver', lang=user.locale) % \
            dict(name=driver['user']['name'])
        badge = redis.\
            incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'slot': 'honk',
            'latitude': driver['user']['latitude'],
            'longitude': driver['user']['longitude'],
            'sound': 'default',
            'vibrate': True,
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
                              [passenger['id']], push_adapter,
                              channel, payload_factory)
    return ret.get()


@celery.task
def NotifyPassengersExpirationTask(passengers):
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
        alert = gettext('alert_expiration', lang=user.locale)
        badge = redis.\
            incr(notificationid_for_user(user.id))
        return json.dumps({
            'badge': badge,
            'channel': channel,
            'slot': 'expired',
            'sound': 'default',
            'vibrate': True,
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
                              [p['id'] for p in passengers],
                              push_adapter, channel, payload_factory)
    return ret.get()


@celery.task
def NotifyUserBonusCreditAddedTask(user, payment):
    channel = web.config.TITANIUM_NOTIFICATION_CHANNEL
    logger = create_logger()
    gettext = create_gettext()
    redis = create_redis()
    logging_subscriber = LoggingSubscriber(logger)
    push_adapter = TitaniumPushNotificationsAdapter()
    notify_user = NotifyUserWorkflow()
    ret = Future()
    alert = gettext('alert_added_bonus_credit', lang=user['locale']) % \
        dict(bonus=payment['bonus_credits'])
    badge = redis.incr(notificationid_for_user(user['id']))

    class NotifyUserSubscriber(object):
        def user_not_found(self, user_id):
            ret.set((None, 'User not found: %(user_id)s' % locals()))

        def failure(self, error):
            ret.set((None, error))

        def success(self):
            ret.set((None, None))

    notify_user.add_subscriber(logging_subscriber,
                               NotifyUserSubscriber())
    notify_user.perform(logger, UsersRepository, user['id'],
                        push_adapter, channel,
                        json.dumps({
                            'badge': badge,
                            'channel': channel,
                            'slot': 'bonus',
                            'bonus': payment['bonus_credits'],
                            'sound': 'default',
                            'vibrate': True,
                            'icon': 'notificationicon',
                            'alert': alert
                        }))
    return ret.get()


@celery.task
def DeactivateExpiredPassengersTask():
    expire_after = web.config.EXPIRE_PASSENGERS_AFTER_MINUTES
    logger = create_logger()
    orm = create_session()
    logging_subscriber = LoggingSubscriber(logger)
    deactivate_passengers = DeactivateExpiredPassengersWorkflow()

    class DeactivatePassengersSubscriber(object):
        def success(self):
            orm.commit()

    deactivate_passengers.add_subscriber(logging_subscriber,
                                         DeactivatePassengersSubscriber())
    deactivate_passengers.perform(logger, orm,
                                  expire_after,
                                  PassengersRepository,
                                  NotifyPassengersExpirationTask,
                                  NotifyDriversDeactivatedPassengerTask)
