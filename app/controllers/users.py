#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from strappon.repositories.drivers import DriversRepository
from strappon.repositories.drive_requests import DriveRequestsRepository
from strappon.repositories.payments import PaymentsRepository
from strappon.repositories.passengers import PassengersRepository
from strappon.repositories.perks import PerksRepository
from strappon.repositories.rates import RatesRepository
from strappon.repositories.users import UsersRepository
from weblib.adapters.social.facebook import FacebookAdapter
from weblib.pubsub import Future
from weblib.pubsub import LoggingSubscriber
from weblib.request_decorators import api
from weblib.request_decorators import authorized
from weblib.utils import jsonify

from app.controllers import ParamAuthorizableController
from app.tasks import NotifyDriversDeactivatedPassengerTask
from app.tasks import NotifyPassengersDriverDeactivatedTask
from app.workflows.drivers import DeactivateDriverWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow
from app.workflows.users import LoginUserWorkflow
from app.workflows.users import ViewUserWorkflow


class ViewUserController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self, user_id):
        if user_id != self.current_user.id:
            raise web.unauthorized()

        logger = LoggingSubscriber(web.ctx.logger)
        view_user = ViewUserWorkflow()
        ret = Future()

        class ViewUserSubscriber(object):
            def not_found(self, user_id):
                raise web.notfound()

            def success(self, blob):
                ret.set(jsonify(user=blob))

        view_user.add_subscriber(logger, ViewUserSubscriber())
        view_user.perform(web.ctx.logger, web.ctx.gettext, UsersRepository,
                          user_id, RatesRepository, DriveRequestsRepository,
                          PerksRepository, PaymentsRepository)
        return ret.get()


class LoginUserController(ParamAuthorizableController):
    @api
    def POST(self):
        data = web.input(acs_id=None, facebook_token=None, locale=None)
        logger = LoggingSubscriber(web.ctx.logger)
        login_authorized = LoginUserWorkflow()
        deactivate_driver = DeactivateDriverWorkflow()
        deactivate_passenger = DeactivatePassengerWorkflow()
        token_future = Future()
        user_future = Future()
        ret = Future()

        class LoginAuthorizedSubscriber(object):
            def internal_error(self):
                web.ctx.orm.rollback()
                raise web.badrequest()

            def invalid_form(self, errors):
                web.ctx.orm.rollback()
                raise web.badrequest()

            def success(self, token, user):
                token_future.set(token)
                user_future.set(user)
                driver_id = user_future.get().active_driver.id \
                    if user_future.get().active_driver is not None else None
                deactivate_driver.\
                    perform(web.ctx.logger, web.ctx.orm,
                            DriversRepository,
                            driver_id,
                            user_future.get(),
                            NotifyPassengersDriverDeactivatedTask)

        class DeactivateDriverSubscriber(object):
            def not_found(self, driver_id):
                self.success()

            def unauthorized(self):
                self.success()

            def success(self):
                passenger_id = user_future.get().active_passenger.id \
                    if user_future.get().active_passenger is not None else None
                deactivate_passenger.\
                    perform(web.ctx.logger, web.ctx.orm,
                            PassengersRepository,
                            passenger_id,
                            user_future.get(),
                            NotifyDriversDeactivatedPassengerTask)

        class DeactivatePassengerSubscriber(object):
            def not_found(self, passenger_id):
                self.success()

            def unauthorized(self):
                self.success()

            def success(self):
                web.ctx.orm.commit()
                ret.set(jsonify(token=token_future.get()))

        login_authorized.add_subscriber(logger, LoginAuthorizedSubscriber())
        deactivate_driver.add_subscriber(logger,
                                         DeactivateDriverSubscriber())
        deactivate_passenger.add_subscriber(logger,
                                            DeactivatePassengerSubscriber())
        login_authorized.perform(web.ctx.orm, web.ctx.logger, UsersRepository,
                                 data.acs_id, FacebookAdapter(),
                                 data.facebook_token, data.locale,
                                 PerksRepository,
                                 web.ctx.default_eligible_driver_perks,
                                 web.ctx.default_active_driver_perks,
                                 web.ctx.default_eligible_passenger_perks,
                                 web.ctx.default_active_passenger_perks)
        return ret.get()
