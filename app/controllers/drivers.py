#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
from datetime import datetime

import web
import weblib
from strappon.repositories.drivers import DriversRepository
from strappon.repositories.drive_requests import DriveRequestsRepository
from strappon.repositories.passengers import PassengersRepository
from strappon.repositories.rates import RatesRepository
from strappon.pubsub import serialize_date
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.tasks import NotifyPassengerDriveRequestPending
from app.tasks import NotifyPassengerDriveRequestCancelledTask
from app.tasks import NotifyPassengersDriverDeactivatedTask
from app.tasks import NotifyDriversDeactivatedPassengerTask
from app.workflows.drivers import AddDriverWorkflow
from app.workflows.drivers import DeactivateDriverWorkflow
from app.workflows.drivers import RateDriveRequestWorkflow
from app.workflows.drive_requests import AddDriveRequestWorkflow
from app.workflows.drive_requests import CancelDriveOfferWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow


class AddDriverController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        outer = self
        passenger_id = self.current_user.active_passenger.id \
            if self.current_user.active_passenger is not None else None
        driver_id = self.current_user.active_driver.id \
            if self.current_user.active_driver is not None else None

        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = DeactivatePassengerWorkflow()
        deactivate_driver = DeactivateDriverWorkflow()
        add_driver = AddDriverWorkflow()
        ret = Future()

        class DeactivatePassengerSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self):
                deactivate_driver.\
                    perform(web.ctx.logger, web.ctx.orm,
                            DriversRepository, driver_id,
                            outer.current_user,
                            NotifyPassengersDriverDeactivatedTask)

        class DeactivateDriverSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self):
                add_driver.perform(web.ctx.gettext, web.ctx.orm,
                                   web.ctx.logger,
                                   web.ctx.redis, web.input(),
                                   DriversRepository,
                                   outer.current_user)

        class AddDriverSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))

            def success(self, driver_id):
                web.ctx.orm.commit()
                url = '/1/drivers/%(id)s/view' % dict(id=driver_id)
                raise weblib.created(url)

        deactivate_passenger.add_subscriber(logger,
                                            DeactivatePassengerSubscriber())
        deactivate_driver.add_subscriber(logger,
                                         DeactivateDriverSubscriber())
        add_driver.add_subscriber(logger, AddDriverSubscriber())
        deactivate_passenger.perform(web.ctx.logger, web.ctx.orm,
                                     PassengersRepository, passenger_id,
                                     self.current_user,
                                     NotifyDriversDeactivatedPassengerTask)
        return ret.get()


class DeactivateDriverController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, driver_id):
        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_driver = DeactivateDriverWorkflow()

        class DeactivateDriverSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()
            def success(self):
                web.ctx.orm.commit()
                raise web.ok()

        deactivate_driver.add_subscriber(logger,
                                         DeactivateDriverSubscriber())
        deactivate_driver.perform(web.ctx.logger, web.ctx.orm,
                                  DriversRepository, driver_id,
                                  self.current_user,
                                  NotifyPassengersDriverDeactivatedTask)


class CancelDriveOfferController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, driver_id, drive_request_id):
        logger = LoggingSubscriber(web.ctx.logger)
        cancel_drive_offer = CancelDriveOfferWorkflow()

        class CancelDriveOfferSubscriber(object):
            def not_found(self, driver_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()
            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        cancel_drive_offer.add_subscriber(logger, CancelDriveOfferSubscriber())
        cancel_drive_offer.perform(web.ctx.orm, web.ctx.logger,
                                   DriversRepository, self.current_user.id,
                                   driver_id, DriveRequestsRepository,
                                   drive_request_id,
                                   NotifyPassengerDriveRequestCancelledTask)


def default_offered_pickup_time(params):
    if 'response_time' not in params:
        return None
    response_time = int(params.response_time)
    if response_time == 0:
        return None
    return serialize_date(datetime.utcnow() + timedelta(minutes=response_time))


class AcceptPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, driver_id, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        add_drive_request = AddDriveRequestWorkflow()
        offered_pickup_time = default_offered_pickup_time(web.input())
        params = web.input(offered_pickup_time=offered_pickup_time)

        class AddDriveRequestSubscriber(object):
            def not_found(self, driver_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()
            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        add_drive_request.add_subscriber(logger, AddDriveRequestSubscriber())
        add_drive_request.perform(web.ctx.gettext, web.ctx.orm, web.ctx.logger,
                                  params, self.current_user,
                                  DriversRepository, driver_id,
                                  PassengersRepository, passenger_id,
                                  DriveRequestsRepository,
                                  NotifyPassengerDriveRequestPending)


class RateDriveRequestController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, driver_id, drive_request_id):
        logger = LoggingSubscriber(web.ctx.logger)
        rate_passenger = RateDriveRequestWorkflow()
        ret = Future()

        class RatePassengerSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))
            def driver_not_found(self, driver_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()
            def drive_request_not_found(self, drive_request_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        rate_passenger.add_subscriber(logger, RatePassengerSubscriber())
        rate_passenger.perform(web.ctx.logger, web.ctx.gettext, web.ctx.orm,
                               self.current_user, web.input(), driver_id,
                               drive_request_id,
                               DriversRepository, DriveRequestsRepository,
                               RatesRepository)
        return ret.get()
