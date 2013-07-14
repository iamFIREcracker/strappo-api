#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.passengers import PassengersRepository
from app.repositories.drive_requests import DriveRequestsRepository
from app.tasks import NotifyDriversTask
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import ActivePassengersWorkflow
from app.workflows.passengers import ViewPassengerWorkflow
from app.workflows.drive_requests import AcceptDriveRequestWorkflow


class ActivePassengersController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        passengers = ActivePassengersWorkflow()
        ret = Future()

        class ActivePassengersSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(passengers=blob))

        passengers.add_subscriber(logger, ActivePassengersSubscriber())
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
        add_passenger.perform(web.ctx.orm, web.ctx.logger, web.input(),
                              PassengersRepository, self.current_user.id,
                              NotifyDriversTask)
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
            def success(self, blob):
                ret.set(jsonify(passenger=blob))

        view_passenger.add_subscriber(logger, ViewPassengerSubscriber())
        view_passenger.perform(web.ctx.logger, PassengersRepository,
                               passenger_id)
        return ret.get()


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
                raise app.weblib.nocontent()

        accept_drive_request.add_subscriber(logger,
                                           AcceptDriveRequestSubscriber())
        accept_drive_request.perform(web.ctx.orm, web.ctx.logger,
                                     PassengersRepository, passenger_id,
                                     self.current_user.id,
                                     DriveRequestsRepository, driver_id)
