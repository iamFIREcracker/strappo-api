#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.utils import storage
from strappon.pubsub import ACSSessionCreator
from strappon.pubsub import ACSUserIdsNotifier
from strappon.pubsub.payments import PaymentForPromoCodeCreator
from strappon.pubsub.payments import PaymentSerializer
from strappon.pubsub.perks import DefaultPerksCreator
from strappon.pubsub.promo_codes import PromoCodeWithNameGetter
from strappon.pubsub.promo_codes import PromoCodeActivator
from strappon.pubsub.promo_codes import PromoCodeSerializer
from strappon.pubsub.promo_codes import \
    UserPromoCodeWithUserIdAndPromoCodeIdGetter
from strappon.pubsub.positions import ClosestRegionGetter
from strappon.pubsub.positions import MultiplePositionsArchiver
from strappon.pubsub.positions import PositionsByUserIdGetter
from strappon.pubsub.positions import PositionCreator
from strappon.pubsub.tokens import TokenCreator
from strappon.pubsub.tokens import TokenSerializer
from strappon.pubsub.tokens import TokensByUserIdGetter
from strappon.pubsub.users import UserCreator
from strappon.pubsub.users import UserEnricherPrivate
from strappon.pubsub.users import UserUpdater
from strappon.pubsub.users import UserWithIdGetter
from strappon.pubsub.users import UserWithFacebookIdGetter
from strappon.pubsub.users import UserWithAcsIdGetter
from strappon.pubsub.users import UserSerializer
from strappon.pubsub.users import UserSerializerPrivate
from strappon.pubsub.users import UsersACSUserIdExtractor
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
from weblib.pubsub import TaskSubmitter

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
                payments_repository, tokens_repository,
                notify_credit_bonus_task):
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
        payment_serializer = PaymentSerializer()
        user_serializer = UserSerializer()
        task_submitter = TaskSubmitter()
        user_updater = UserUpdater()
        tokens_getter = TokensByUserIdGetter()
        token_creator = TokenCreator()
        token_serializer = TokenSerializer()
        form_future = Future()
        user_future = Future()
        payment_future = Future()

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
                payment_serializer.perform(payment)

        class PaymentSerializerSubscriber(object):
            def payment_serialized(self, payment):
                payment_future.set(payment)
                user_serializer.perform(user_future.get())

        class UserSerializerSubscriber(object):
            def user_serialized(self, user):
                task_submitter.perform(notify_credit_bonus_task, user,
                                       payment_future.get())

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                tokens_getter.perform(tokens_repository, user_future.get().id)

        class UserUpdaterSubscriber(object):
            def user_updated(self, user):
                orm.add(user)
                user_future.set(user)
                tokens_getter.perform(tokens_repository, user.id)

        class TokensGettetSubscriber(object):
            def tokens_found(self, tokens):
                for t in tokens:
                    orm.delete(t)
                token_creator.perform(tokens_repository, user_future.get().id)

        class TokenCreatorSubscriber(object):
            def token_created(self, token):
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
        payment_serializer.add_subscriber(logger,
                                          PaymentSerializerSubscriber())
        user_serializer.add_subscriber(logger, UserSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        user_updater.add_subscriber(logger, UserUpdaterSubscriber())
        tokens_getter.add_subscriber(logger, TokensGettetSubscriber())
        token_creator.add_subscriber(logger, TokenCreatorSubscriber())
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
        positions_getter = PositionsByUserIdGetter()
        positions_archiver = MultiplePositionsArchiver()
        position_creator = PositionCreator()
        form_future = Future()
        region_future = Future()

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
                region_future.set('Unknown')
                positions_getter.perform(positions_repository,
                                         user.id)

            def region_found(self, region):
                region_future.set(region)
                positions_getter.perform(positions_repository,
                                         user.id)

        class PositionsGetterSubscriber(object):
            def positions_found(self, positions):
                positions_archiver.perform(positions)

        class PositionsArchiverSubscriber(object):
            def positions_archived(self, positions):
                orm.add_all(positions)
                position_creator.perform(positions_repository,
                                         user.id,
                                         region_future.get(),
                                         float(form_future.get().d.latitude),
                                         float(form_future.get().d.longitude))

        class PositionCreatorSubscriber(object):
            def position_created(self, position):
                user.position = position
                orm.add(position)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        region_getter.add_subscriber(logger, RegionGetterSubscriber())
        positions_getter.add_subscriber(logger, PositionsGetterSubscriber())
        positions_archiver.add_subscriber(logger,
                                          PositionsArchiverSubscriber())
        position_creator.add_subscriber(logger, PositionCreatorSubscriber())
        form_validator.perform(position_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))


class NotifyUserWorkflow(Publisher):
    def perform(self, logger, users_repository, user_id, push_adapter,
                channel, payload):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_getter = UserWithIdGetter()
        acs_ids_extractor = UsersACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSUserIdsNotifier()
        user_ids_future = Future()

        class UserGetterSubscriber(object):
            def user_not_found(self, user_id):
                outer.publish('user_not_found', user_id)

            def user_found(self, user):
                acs_ids_extractor.perform([user])

        class ACSUserIdsExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                user_ids_future.set(user_ids)
                acs_session_creator.perform(push_adapter)

        class ACSSessionCreatorSubscriber(object):
            def acs_session_not_created(self, error):
                outer.publish('failure', error)

            def acs_session_created(self, session_id):
                acs_notifier.perform(push_adapter, session_id, channel,
                                     user_ids_future.get(), payload)

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)

            def acs_user_ids_notified(self):
                outer.publish('success')

        user_getter.add_subscriber(logger, UserGetterSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdsExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        user_getter.perform(users_repository, user_id)
