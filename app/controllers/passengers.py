#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.passengers import PassengersRepository
from app.repositories.drive_requests import DriveRequestsRepository
from app.tasks import NotifyDriverDriveRequestCancelledByPassengerTask
from app.tasks import NotifyDriverDriveRequestAccepted
from app.tasks import NotifyDriversPassengerRegisteredTask
from app.tasks import NotifyDriversPassengerAlitTask
from app.tasks import NotifyDriversDeactivatedPassengerTask
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import ListUnmatchedPassengersWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow
from app.workflows.passengers import ViewPassengerWorkflow
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
        passengers.perform(web.ctx.logger, PassengersRepository)
        return ret.get()


class AddPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self):
        logger = LoggingSubscriber(web.ctx.logger)
        add_passenger = AddPassengerWorkflow()
        ret = Future()

        class AddPassengerSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))
            def success(self, passenger_id):
                web.ctx.orm.commit()
                url = '/1/passengers/%(id)s/view' % dict(id=passenger_id)
                raise app.weblib.created(url)

        add_passenger.add_subscriber(logger, AddPassengerSubscriber())
        add_passenger.perform(web.ctx.gettext, web.ctx.orm, web.ctx.logger,
                              web.ctx.redis, web.input(), PassengersRepository,
                              self.current_user,
                              NotifyDriversPassengerRegisteredTask)
        return ret.get()


class ViewPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        view_passenger = ViewPassengerWorkflow()
        ret = Future()

        class ViewPassengerSubscriber(object):
            def not_found(self, passenger_id):
                raise web.notfound()
            def unauthorized(self):
                raise web.unauthorized()
            def success(self, blob):
                ret.set(jsonify(passenger=blob))

        view_passenger.add_subscriber(logger, ViewPassengerSubscriber())
        view_passenger.perform(web.ctx.logger, PassengersRepository,
                               passenger_id, self.current_user.id)
        return ret.get()


class AlightPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = DeactivatePassengerWorkflow()

        class DeactivatePassengerSubscriber(object):
            def not_found(self, passenger_id):
                raise web.notfound()
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
                                     NotifyDriversPassengerAlitTask)



class DeactivatePassengerController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        deactivate_passenger = DeactivatePassengerWorkflow()

        class DeactivatePassengerSubscriber(object):
            def not_found(self, passenger_id):
                raise web.notfound()
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
            def not_found(self, passenger_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def unauthorized(self):
                web.ctx.orm.rollback()
                raise web.unauthorized()
            def success(self):
                web.ctx.orm.commit()
                raise app.weblib.nocontent()

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
                raise app.weblib.nocontent()

        cancel_drive_request.add_subscriber(logger, CancelDriveRequestSubscriber())
        cancel_drive_request.perform(web.ctx.orm, web.ctx.logger,
                                     PassengersRepository, self.current_user.id,
                                     passenger_id, DriveRequestsRepository,
                                     drive_request_id,
                                     NotifyDriverDriveRequestCancelledByPassengerTask)
