#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import weblib
from strappon.repositories.drive_requests import DriveRequestsRepository
from strappon.repositories.passengers import PassengersRepository
from strappon.repositories.payments import PaymentsRepository
from strappon.repositories.perks import PerksRepository
from strappon.repositories.rates import RatesRepository
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.tasks import NotifyDriverDriveRequestCancelledByPassengerTask
from app.tasks import NotifyDriverDriveRequestAccepted
from app.tasks import NotifyDriversPassengerRegisteredTask
from app.tasks import NotifyDriversPassengerAlitTask
from app.tasks import NotifyDriversDeactivatedPassengerTask
from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import AlightPassengerWorkflow
from app.workflows.passengers import CalculateFareWorkflow
from app.workflows.passengers import ListUnmatchedPassengersWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow
from app.workflows.drive_requests import AcceptDriveRequestWorkflow
from app.workflows.drive_requests import CancelDriveRequestWorkflow


class ListUnmatchedPassengersController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        passengers = ListUnmatchedPassengersWorkflow()
        ret = Future()

        class ListUnmatchedPassengersSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(passengers=blob))

        passengers.add_subscriber(logger, ListUnmatchedPassengersSubscriber())
        passengers.perform(web.ctx.logger, PassengersRepository,
                           RatesRepository, PerksRepository,
                           self.current_user.id)
        return ret.get()


class AddPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        outer = self
        passenger_id = self.current_user.active_passenger.id \
            if self.current_user.active_passenger is not None else None

        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = DeactivatePassengerWorkflow()
        add_passenger = AddPassengerWorkflow()
        ret = Future()

        class DeactivatePassengerSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self):
                add_passenger.perform(web.ctx.gettext, web.ctx.orm,
                                      web.ctx.logger,
                                      web.ctx.redis, web.input(),
                                      PassengersRepository,
                                      outer.current_user,
                                      NotifyDriversPassengerRegisteredTask)

        class AddPassengerSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))

            def success(self, passenger_id):
                web.ctx.orm.commit()
                url = '/1/passengers/%(id)s/view' % dict(id=passenger_id)
                raise weblib.created(url)

        deactivate_passenger.add_subscriber(logger,
                                            DeactivatePassengerSubscriber())
        add_passenger.add_subscriber(logger, AddPassengerSubscriber())
        deactivate_passenger.perform(web.ctx.logger, web.ctx.orm,
                                     PassengersRepository, passenger_id,
                                     self.current_user,
                                     NotifyDriversDeactivatedPassengerTask)
        return ret.get()


class AlightPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = AlightPassengerWorkflow()
        ret = Future()

        class DeactivatePassengerSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))

            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()

            def success(self):
                web.ctx.orm.commit()
                raise web.ok()

        deactivate_passenger.add_subscriber(logger,
                                            DeactivatePassengerSubscriber())
        deactivate_passenger.perform(web.ctx.logger, web.ctx.gettext,
                                     web.ctx.orm, web.input(),
                                     RatesRepository, PassengersRepository,
                                     PerksRepository, PaymentsRepository,
                                     passenger_id, self.current_user,
                                     NotifyDriversPassengerAlitTask)
        return ret.get()


class DeactivatePassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = DeactivatePassengerWorkflow()

        class DeactivatePassengerSubscriber(object):
            def unauthorized(self):
                raise web.unauthorized()

            def success(self):
                web.ctx.orm.commit()
                raise web.ok()

        deactivate_passenger.add_subscriber(logger,
                                            DeactivatePassengerSubscriber())
        deactivate_passenger.perform(web.ctx.logger, web.ctx.orm,
                                     PassengersRepository, passenger_id,
                                     self.current_user,
                                     NotifyDriversDeactivatedPassengerTask)


class AcceptDriverController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id, driver_id):
        logger = LoggingSubscriber(web.ctx.logger)
        accept_drive_request = AcceptDriveRequestWorkflow()

        class AcceptDriveRequestSubscriber(object):
            def not_found(self):
                web.ctx.orm.rollback()
                raise web.notfound()

            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()

            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        accept_drive_request.add_subscriber(logger,
                                            AcceptDriveRequestSubscriber())
        accept_drive_request.perform(web.ctx.orm, web.ctx.logger,
                                     PassengersRepository, passenger_id,
                                     self.current_user.id,
                                     DriveRequestsRepository, driver_id,
                                     NotifyDriverDriveRequestAccepted)


class CancelDriveRequestController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id, drive_request_id):
        logger = LoggingSubscriber(web.ctx.logger)
        cancel_drive_request = CancelDriveRequestWorkflow()

        class CancelDriveRequestSubscriber(object):
            def not_found(self, driver_id):
                web.ctx.orm.rollback()
                raise web.notfound()

            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()

            def success(self):
                web.ctx.orm.commit()
                raise weblib.nocontent()

        cancel_drive_request.add_subscriber(logger,
                                            CancelDriveRequestSubscriber())
        cancel_drive_request.\
            perform(web.ctx.orm, web.ctx.logger,
                    PassengersRepository,
                    self.current_user.id,
                    passenger_id, DriveRequestsRepository,
                    drive_request_id,
                    NotifyDriverDriveRequestCancelledByPassengerTask)


class CalculateFareController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        calculate_fare = CalculateFareWorkflow()
        ret = Future()

        class CalculateFareSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))

            def success(self, fare):
                ret.set(jsonify(fare=fare))

        calculate_fare.add_subscriber(logger, CalculateFareSubscriber())
        calculate_fare.perform(web.ctx.gettext, web.ctx.logger, web.input(),
                               PerksRepository, self.current_user)
        return ret.get()
