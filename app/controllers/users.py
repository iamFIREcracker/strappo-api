#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import weblib
from strappon.repositories.drivers import DriversRepository
from strappon.repositories.drive_requests import DriveRequestsRepository
from strappon.repositories.payments import PaymentsRepository
from strappon.repositories.passengers import PassengersRepository
from strappon.repositories.perks import PerksRepository
from strappon.repositories.promo_codes import PromoCodesRepository
from strappon.repositories.positions import PositionsRepository
from strappon.repositories.rates import RatesRepository
from strappon.repositories.tokens import TokensRepository
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
from app.tasks import NotifyUserBonusCreditAddedTask
from app.workflows.drivers import DeactivateDriverWorkflow
from app.workflows.passengers import DeactivatePassengerWorkflow
from app.workflows.users import ActivatePromoCodeWorkflow
from app.workflows.users import ListMutualFriendsWorkflow
from app.workflows.users import LoginUserWorkflow
from app.workflows.users import UpdatePositionWorkflow
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
                                 web.ctx.default_active_passenger_perks,
                                 PromoCodesRepository,
                                 web.ctx.default_promo_code,
                                 PaymentsRepository,
                                 TokensRepository,
                                 NotifyUserBonusCreditAddedTask)
        return ret.get()


class ListMutualFriendsController(ParamAuthorizableController):
    @api
    @authorized
    def GET(self, user_id):
        if user_id != self.current_user.id:
            raise web.unauthorized()

        data = web.input(with_user=None)
        logger = LoggingSubscriber(web.ctx.logger)
        list_mutual_friends = ListMutualFriendsWorkflow()
        ret = Future()

        class ListMutualFriendsSubscriber(object):
            def success(self, blob):
                ret.set(jsonify(mutual_friends=blob))

        list_mutual_friends.add_subscriber(logger,
                                           ListMutualFriendsSubscriber())
        list_mutual_friends.perform(web.ctx.logger, web.ctx.redis,
                                    UsersRepository, self.current_user,
                                    FacebookAdapter(),
                                    web.config.FACEBOOK_APP_SECRET,
                                    self.current_user.facebook_token,
                                    data.with_user,
                                    web.config.FACEBOOK_CACHE_EXPIRE_SECONDS)
        return ret.get()


class UpdatePositionController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, user_id):
        if user_id != self.current_user.id:
            raise web.unauthorized()

        logger = LoggingSubscriber(web.ctx.logger)
        update_position = UpdatePositionWorkflow()
        ret = Future()

        class UpdatePositionSubscriber(object):
            def invalid_form(self, blob):
                web.ctx.orm.rollback()
                ret.set(jsonify(blob))

            def success(self):
                web.ctx.orm.commit()
                raise web.ok()

        update_position.add_subscriber(logger,
                                       UpdatePositionSubscriber())
        update_position.perform(web.ctx.gettext, web.ctx.orm, web.ctx.logger,
                                self.current_user,
                                web.input(latitude=None, longitude=None),
                                PositionsRepository,
                                web.config.APP_SERVED_REGIONS)
        return ret.get()


class ActivatePromoCodeController(ParamAuthorizableController):
    @api
    @authorized
    def POST(self, user_id):
        if user_id != self.current_user.id:
            raise web.unauthorized()

        logger = LoggingSubscriber(web.ctx.logger)
        activate_promo_code = ActivatePromoCodeWorkflow()
        ret = Future()

        class ActivatePromoCodeSubscriber(object):
            def not_found(self, name):
                web.ctx.orm.rollback()
                raise web.notfound()

            def already_activated(self):
                web.ctx.orm.rollback()
                raise weblib.nocontent()

            def success(self, blob):
                web.ctx.orm.commit()
                ret.set(jsonify(promo_code=blob))

        activate_promo_code.add_subscriber(logger,
                                           ActivatePromoCodeSubscriber())
        activate_promo_code.perform(web.ctx.orm, web.ctx.logger,
                                    self.current_user.id,
                                    web.input(name='').name,
                                    PromoCodesRepository, PaymentsRepository)
        return ret.get()
