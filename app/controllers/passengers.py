#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.passengers import PassengersRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.passengers import AddPassengerWorkflow
from app.workflows.passengers import PassengersWorkflow
from app.workflows.passengers import ViewPassengerWorkflow


class PassengersController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        drivers = PassengersWorkflow()
        ret = Future()

        class PassengersSubscriber(object):
            def not_found(self, driver_id):
                ret.set(jsonify(passengers=[]))
            def success(self, blob):
                ret.set(jsonify(passengers=blob))

        drivers.add_subscriber(logger, PassengersSubscriber())
        drivers.perform(web.ctx.logger, PassengersRepository)
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
                              PassengersRepository, self.current_user.id)
        return ret.get()


class ViewPassengerController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self, passenger_id):
        logger = LoggingSubscriber(web.ctx.logger)
        view_driver = ViewPassengerWorkflow()
        ret = Future()

        class ViewPassengerSubscriber(object):
            def not_found(self, driver_id):
                raise web.notfound()
            def success(self, blob):
                ret.set(jsonify(passenger=blob))

        view_driver.add_subscriber(logger, ViewPassengerSubscriber())
        view_driver.perform(web.ctx.logger, PassengersRepository, passenger_id)
        return ret.get()
