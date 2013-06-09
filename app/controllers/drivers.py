#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

import app.weblib
from app.controllers import ParamAuthorizableController
from app.repositories.drivers import DriversRepository
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.request_decorators import api
from app.weblib.request_decorators import authorized
from app.weblib.utils import jsonify
from app.workflows.drivers import EditDriverWorkflow
from app.workflows.drivers import DriversWithUserIdWorkflow


class DriversController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        drivers = DriversWithUserIdWorkflow()
        ret = Future()

        class DriversWithUserIdSubscriber(object):
            def not_found(self, driver_id):
                ret.set(jsonify(drivers=[]))
            def success(self, blob):
                ret.set(jsonify(drivers=[blob]))

        drivers.add_subscriber(logger, DriversWithUserIdSubscriber())
        drivers.perform(web.ctx.logger, DriversRepository,
                        web.input(user_id=None).user_id)
        return ret.get()


class EditDriverController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, driver_id):
        logger = LoggingSubscriber(web.ctx.logger)
        edit_driver = EditDriverWorkflow()
        ret = Future()

        class EditDriverSubscriber(object):
            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                ret.set(jsonify(success=False, errors=errors))
            def not_found(self, driver_id):
                web.ctx.orm.rollback()
                raise web.notfound()
            def success(self):
                web.ctx.orm.commit()
                raise app.weblib.nocontent()

        edit_driver.add_subscriber(logger, EditDriverSubscriber())
        edit_driver.perform(web.ctx.orm, web.ctx.logger, web.input(),
                            DriversRepository, driver_id)
        return ret.get()
