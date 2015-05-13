#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.utils import storage
from strappon.pubsub.users import TokenRefresher
from strappon.pubsub.users import TokenSerializer
from strappon.pubsub.users import UserCreator
from strappon.pubsub.users import UserEnricherPrivate
from strappon.pubsub.users import UserUpdater
from strappon.pubsub.users import UserWithIdGetter
from strappon.pubsub.users import UserWithFacebookIdGetter
from strappon.pubsub.users import UserWithAcsIdGetter
from strappon.pubsub.users import UserSerializerPrivate
from strappon.pubsub.payments import PaymentForPromoCodeCreator
from strappon.pubsub.perks import DefaultPerksCreator
from strappon.pubsub.promo_codes import PromoCodeWithNameGetter
from strappon.pubsub.promo_codes import PromoCodeActivator
from strappon.pubsub.promo_codes import PromoCodeSerializer
from strappon.pubsub.promo_codes import \
    UserPromoCodeWithUserIdAndPromoCodeIdGetter
from strappon.pubsub.positions import ClosestRegionGetter
from strappon.pubsub.positions import PositionCreator
from weblib.adapters.social.facebook import CachedFacebookMutualFriendsGetter
from weblib.adapters.social.facebook import CachedFacebookMutualFriendsSetter
from weblib.adapters.social.facebook import FacebookMutualFriendsGetter
from weblib.adapters.social.facebook import FacebookProfileGetter
from weblib.forms import describe_invalid_form
from weblib.forms import describe_invalid_form_localized
from weblib.pubsub import FormValidator
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher
from weblib.pubsub import Future

import app.forms.positions as position_forms
import app.forms.users as user_forms


class ViewUserWorkflow(Publisher):
    """Defines a workflow to view the details of an active user."""

    def perform(self, logger, gettext, users_repository, user_id,
                rates_repository, drive_requests_repository,
                perks_repository, payments_repository):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_getter = UserWithIdGetter()
        user_enricher = UserEnricherPrivate()
        user_serializer = UserSerializerPrivate()

        class UserGetterSubscriber(object):
            def user_not_found(self, user_id):
                outer.publish('not_found', user_id)

            def user_found(self, user):
                user_enricher.perform(rates_repository,
                                      drive_requests_repository,
                                      perks_repository,
                                      payments_repository,
                                      user)

        class UserEnricherSubscriber(object):
            def user_enriched(self, user):
                user_serializer.perform(gettext, user)

        class UsersSerializerSubscriber(object):
            def user_serialized(self, blob):
                outer.publish('success', blob)

        user_getter.add_subscriber(logger, UserGetterSubscriber())
        user_enricher.add_subscriber(logger, UserEnricherSubscriber())
        user_serializer.add_subscriber(logger, UsersSerializerSubscriber())
        user_getter.perform(users_repository, user_id)


class ListMutualFriendsWorkflow(Publisher):
    def perform(self, logger, redis, users_repository, user,
                facebook_adapter, app_secret,
                access_token, other_user_id,
                cache_expire_seconds):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_getter = UserWithIdGetter()
        cached_mutual_friends_getter = CachedFacebookMutualFriendsGetter()
        mutual_friends_getter = FacebookMutualFriendsGetter()
        cached_mutual_friends_setter = CachedFacebookMutualFriendsSetter()
        other_facebook_id_future = Future()
        mutual_friends_future = Future()

        class UserGetterSubscriber(object):
            def user_not_found(self, user_id):
                outer.publish('success', dict(data=[],
                                              summary=dict(total_count=0)))

            def user_found(self, other_user):
                other_facebook_id_future.set(other_user.facebook_id)
                cached_mutual_friends_getter.perform(redis,
                                                     user.facebook_id,
                                                     other_user.facebook_id)

        class CachedMutualFriendsGetterSubscriber(object):
            def cached_mutual_friends_not_found(self, cache_id):
                mutual_friends_getter.perform(facebook_adapter,
                                              app_secret,
                                              access_token,
                                              other_facebook_id_future.get())

            def cached_mutual_friends_found(self, mutual_friends):
                outer.publish('success', mutual_friends)

        class MutualFriendsGetterSubscriber(object):
            def mutual_friends_not_found(self, error):
                outer.publish('success', dict(data=[],
                                              summary=dict(total_count=0)))

            def mutual_friends_found(self, mutual_friends):
                mutual_friends_future.set(mutual_friends)
                cached_mutual_friends_setter.\
                    perform(redis,
                            user.facebook_id,
                            other_facebook_id_future.get(),
                            mutual_friends,
                            cache_expire_seconds)

        class CachedMutualFriendsSetterSubscriber(object):
            def cached_mutual_friends_set(self, cache_id):
                outer.publish('success', mutual_friends_future.get())

        user_getter.add_subscriber(logger, UserGetterSubscriber())
        cached_mutual_friends_getter.\
            add_subscriber(logger, CachedMutualFriendsGetterSubscriber())
        mutual_friends_getter.add_subscriber(logger,
                                             MutualFriendsGetterSubscriber())
        cached_mutual_friends_setter.\
            add_subscriber(logger, CachedMutualFriendsSetterSubscriber())
        user_getter.perform(users_repository, other_user_id)


class LoginUserWorkflow(Publisher):
    """Defines a workflow managing the user login process."""

    def perform(self, orm, logger, users_repository, acs_id, facebook_adapter,
                facebook_token, locale, perks_repository,
                eligible_driver_perks, active_driver_perks,
                eligible_passenger_perks, active_passenger_perks,
                promo_codes_repository, default_promo_code,
                payments_repository):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        profile_getter = FacebookProfileGetter()
        form_validator = FormValidator()
        user_with_facebook_id_getter = UserWithFacebookIdGetter()
        user_with_acs_id_getter = UserWithAcsIdGetter()
        user_creator = UserCreator()
        default_perks_creator = DefaultPerksCreator()
        promo_code_activator = PromoCodeActivator()
        payment_creator = PaymentForPromoCodeCreator()
        user_updater = UserUpdater()
        token_refresher = TokenRefresher()
        token_serializer = TokenSerializer()
        form_future = Future()
        user_future = Future()

        class ProfileGetterSubscriber(object):
            def profile_not_found(self, error):
                outer.publish('internal_error')

            def profile_found(self, profile):
                params = \
                    storage(acs_id=acs_id,
                            facebook_id=profile['id'],
                            first_name=profile['first_name'],
                            last_name=profile['last_name'],
                            name=profile['name'],
                            avatar_unresolved=profile['avatar_unresolved'],
                            avatar=profile['avatar'],
                            email=profile['email'],
                            locale=locale)
                form_validator.perform(user_forms.add(), params,
                                       describe_invalid_form)

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))

            def valid_form(self, form):
                form_future.set(form)
                user_with_facebook_id_getter.perform(users_repository,
                                                     form.d.facebook_id)

        class UserWithFacebookIdGetterSubscriber(object):
            def user_found(self, user):
                form = form_future.get()
                user_updater.perform(user,
                                     form.d.acs_id,
                                     form.d.facebook_id,
                                     facebook_token,
                                     form.d.first_name,
                                     form.d.last_name,
                                     form.d.name,
                                     form.d.avatar_unresolved,
                                     form.d.avatar,
                                     form.d.email,
                                     form.d.locale)

            def user_not_found(self, facebook_id):
                form = form_future.get()
                user_with_acs_id_getter.perform(users_repository,
                                                form.d.acs_id)

        class UserWithAcsIdGetterSubscriber(object):
            def user_found(self, user):
                form = form_future.get()
                user_updater.perform(user,
                                     form.d.acs_id,
                                     form.d.facebook_id,
                                     facebook_token,
                                     form.d.first_name,
                                     form.d.last_name,
                                     form.d.name,
                                     form.d.avatar_unresolved,
                                     form.d.avatar,
                                     form.d.email,
                                     form.d.locale)

            def user_not_found(self, acs_id):
                form = form_future.get()
                user_creator.perform(users_repository,
                                     form.d.acs_id,
                                     form.d.facebook_id,
                                     facebook_token,
                                     form.d.first_name,
                                     form.d.last_name,
                                     form.d.name,
                                     form.d.avatar_unresolved,
                                     form.d.avatar,
                                     form.d.email,
                                     form.d.locale)

        class UserCreatorSubscriber(object):
            def user_created(self, user):
                orm.add(user)
                user_future.set(user)
                default_perks_creator.perform(perks_repository,
                                              user,
                                              eligible_driver_perks,
                                              active_driver_perks,
                                              eligible_passenger_perks,
                                              active_passenger_perks)

        class DefaultPerksCreatorSubscriber(object):
            def perks_created(self, perks):
                orm.add_all(perks)
                promo_code_activator.perform(promo_codes_repository,
                                             user_future.get().id,
                                             default_promo_code.id)

        class PromoCodeActivatorSubscriber(object):
            def user_promo_code_activated(self, user_promo_code):
                orm.add(user_promo_code)
                payment_creator.perform(payments_repository,
                                        user_future.get().id,
                                        default_promo_code)

        class PaymentsCreatorSubscriber(object):
            def payment_created(self, payment):
                orm.add(payment)
                token_refresher.perform(users_repository, user_future.get().id)

        class UserUpdaterSubscriber(object):
            def user_updated(self, user):
                orm.add(user)
                user_future.set(user)
                token_refresher.perform(users_repository, user.id)

        class TokenRefresherSubscriber(object):
            def token_refreshed(self, token):
                orm.add(token)
                token_serializer.perform(token)

        class TokenSerializerSubscriber(object):
            def token_serialized(self, blob):
                outer.publish('success', blob, user_future.get())

        profile_getter.add_subscriber(logger, ProfileGetterSubscriber())
        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        user_with_facebook_id_getter.\
            add_subscriber(logger, UserWithFacebookIdGetterSubscriber())
        user_with_acs_id_getter.\
            add_subscriber(logger, UserWithAcsIdGetterSubscriber())
        user_creator.add_subscriber(logger, UserCreatorSubscriber())
        default_perks_creator.add_subscriber(logger,
                                             DefaultPerksCreatorSubscriber())
        promo_code_activator.add_subscriber(logger,
                                            PromoCodeActivatorSubscriber())
        payment_creator.add_subscriber(logger, PaymentsCreatorSubscriber())
        user_updater.add_subscriber(logger, UserUpdaterSubscriber())
        token_refresher.add_subscriber(logger, TokenRefresherSubscriber())
        token_serializer.add_subscriber(logger, TokenSerializerSubscriber())
        profile_getter.perform(facebook_adapter, facebook_token)


class ActivatePromoCodeWorkflow(Publisher):
    def perform(self, orm, logger, user_id, name, promo_codes_repository,
                payments_repository):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        promo_code_getter = PromoCodeWithNameGetter()
        user_promo_code_getter = UserPromoCodeWithUserIdAndPromoCodeIdGetter()
        promo_code_activator = PromoCodeActivator()
        payment_creator = PaymentForPromoCodeCreator()
        promo_code_serializer = PromoCodeSerializer()
        promo_code_future = Future()

        class PromoCodeGetterSubscriber(object):
            def promo_code_not_found(self, name):
                outer.publish('not_found', name)

            def promo_code_found(self, promo_code):
                promo_code_future.set(promo_code)
                user_promo_code_getter.perform(promo_codes_repository,
                                               user_id, promo_code.id)

        class UserPromoCodeGetterSubscriber(object):
            def user_promo_code_found(self, user_promo_code):
                outer.publish('already_activated')

            def user_promo_code_not_found(self, user_id, promo_code_id):
                promo_code_activator.perform(promo_codes_repository,
                                             user_id, promo_code_id)

        class PromoCodeActivatorSubscriber(object):
            def user_promo_code_activated(self, user_promo_code):
                orm.add(user_promo_code)
                payment_creator.perform(payments_repository,
                                        user_id, promo_code_future.get())

        class PaymentsCreatorSubscriber(object):
            def payment_created(self, payment):
                orm.add(payment)
                promo_code_serializer.perform(promo_code_future.get())

        class PromoCodeSerializerSubscriber(object):
            def promo_code_serialized(self, blob):
                outer.publish('success', blob)

        promo_code_getter.add_subscriber(logger,
                                         PromoCodeGetterSubscriber())
        user_promo_code_getter.add_subscriber(logger,
                                              UserPromoCodeGetterSubscriber())
        promo_code_activator.add_subscriber(logger,
                                            PromoCodeActivatorSubscriber())
        payment_creator.add_subscriber(logger, PaymentsCreatorSubscriber())
        promo_code_serializer.add_subscriber(logger,
                                             PromoCodeSerializerSubscriber())
        promo_code_getter.perform(promo_codes_repository, name)


class UpdatePositionWorkflow(Publisher):
    def perform(self, gettext, orm, logger, user, params,
                positions_repository, served_regions):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        region_getter = ClosestRegionGetter()
        position_creator = PositionCreator()
        form_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))

            def valid_form(self, form):
                form_future.set(form)
                region_getter.perform(served_regions,
                                      float(form.d.latitude),
                                      float(form.d.longitude))

        class RegionGetterSubscriber(object):
            def region_not_found(self, latitude, longitude):
                outer.publish('success')

            def region_found(self, region):
                position_creator.perform(positions_repository,
                                         user.id,
                                         region,
                                         float(form_future.get().d.latitude),
                                         float(form_future.get().d.longitude))

        class PositionCreatorSubscriber(object):
            def position_created(self, position):
                orm.add(position)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        region_getter.add_subscriber(logger, RegionGetterSubscriber())
        position_creator.add_subscriber(logger, PositionCreatorSubscriber())
        form_validator.perform(position_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))
