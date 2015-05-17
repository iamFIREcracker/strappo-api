#!/usr/bin/env python
# -*- coding: utf-8 -*-


from strappon.pubsub import ACSSessionCreator
from strappon.pubsub import ACSPayloadsForUserIdNotifier
from strappon.pubsub import DistanceCalculator
from strappon.pubsub import PayloadsByUserCreator
from strappon.pubsub.drive_requests import AcceptedDriveRequestsFilter
from strappon.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from strappon.pubsub.drive_requests import MultipleDriveRequestsCancellor
from strappon.pubsub.drive_requests import MultipleDriveRequestsSerializer
from strappon.pubsub.notifications import NotificationsResetter
from strappon.pubsub.passengers import ExpiredPassengersGetter
from strappon.pubsub.passengers import ActivePassengerWithIdGetter
from strappon.pubsub.passengers import PassengerWithIdGetter
from strappon.pubsub.passengers import MultiplePassengersWithIdGetter
from strappon.pubsub.passengers import MultiplePassengersDeactivator
from strappon.pubsub.passengers import MultiplePassengersSerializer
from strappon.pubsub.passengers import PassengersACSUserIdExtractor
from strappon.pubsub.passengers import PassengerCreator
from strappon.pubsub.passengers import PassengerCopier
from strappon.pubsub.passengers import PassengersEnricher
from strappon.pubsub.passengers import PassengerSerializer
from strappon.pubsub.passengers import PassengerWithUserIdAuthorizer
from strappon.pubsub.passengers import UnmatchedPassengersGetter
from strappon.pubsub.passengers import UnmatchedPassengersByRegionGetter
from strappon.pubsub.payments import ReimbursementCalculator
from strappon.pubsub.payments import ReimbursementCreator
from strappon.pubsub.payments import FareCalculator
from strappon.pubsub.payments import FareCreator
from strappon.pubsub.payments import CreditsByUserIdGetter
from strappon.pubsub.payments import CreditsReserver
from strappon.pubsub.perks import ActiveDriverPerksGetter
from strappon.pubsub.perks import ActivePassengerPerksGetter
from strappon.pubsub.rates import RateCreator
from strappon.pubsub.users import UserRegionExtractor
from weblib.forms import describe_invalid_form_localized
from weblib.pubsub import FormValidator
from weblib.pubsub import Publisher
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import TaskSubmitter
from weblib.pubsub import Future

import app.forms.passengers as passengers_forms
import app.forms.rates as rates_forms
from app.forms import datetime_parser


class ListUnmatchedPassengersWorkflow(Publisher):
    """Defines a workflow to view the list of unmatched passengers."""

    def perform(self, logger, passengers_epository, rates_repository,
                perks_repository, user):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_region_extractor = UserRegionExtractor()
        passengers_getter = UnmatchedPassengersGetter()
        passengers_by_region_getter = UnmatchedPassengersByRegionGetter()
        active_driver_perks_getter = ActiveDriverPerksGetter()
        passengers_enricher = PassengersEnricher()
        passengers_serializer = MultiplePassengersSerializer()
        passengers_future = Future()

        class UserRegionExtractorSubscriber(object):
            def region_not_found(self):
                passengers_getter.perform(passengers_epository)

            def region_found(self, region):
                passengers_by_region_getter.perform(passengers_epository,
                                                    region)

        class ActivePassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_future.set(passengers)
                active_driver_perks_getter.perform(perks_repository,
                                                   user.id)

        class ActivePassengersByRegionGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_future.set(passengers)
                active_driver_perks_getter.perform(perks_repository,
                                                   user.id)

        class ActiveDriverPerksGetterSubscriber(object):
            def active_driver_perks_found(self, passenger_perks):
                passengers_enricher.\
                    perform(rates_repository,
                            passenger_perks[0].perk.fixed_rate,
                            passenger_perks[0].perk.multiplier,
                            passengers_future.get())

        class PassengersEnricherSubscriber(object):
            def passengers_enriched(self, passengers):
                passengers_serializer.perform(passengers)

        class PassengersSerializerSubscriber(object):
            def passengers_serialized(self, blob):
                outer.publish('success', blob)

        user_region_extractor.add_subscriber(logger,
                                             UserRegionExtractorSubscriber())
        passengers_getter.add_subscriber(logger,
                                         ActivePassengersGetterSubscriber())
        passengers_by_region_getter.\
            add_subscriber(logger,
                           ActivePassengersByRegionGetterSubscriber())
        active_driver_perks_getter.\
            add_subscriber(logger, ActiveDriverPerksGetterSubscriber())
        passengers_enricher.add_subscriber(logger,
                                           PassengersEnricherSubscriber())
        passengers_serializer.add_subscriber(logger,
                                             PassengersSerializerSubscriber())
        user_region_extractor.perform(user)


class AddPassengerWorkflow(Publisher):
    """Defines a workflow to add a new passenger."""

    def perform(self, gettext, orm, logger, redis, params,
                passengers_repository, perks_repository,
                payments_repository, user, task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        distance_calculator = DistanceCalculator()
        active_passenger_perks_getter = ActivePassengerPerksGetter()
        fare_calculator = FareCalculator()
        credits_getter = CreditsByUserIdGetter()
        credits_reserver = CreditsReserver()
        passenger_creator = PassengerCreator()
        passenger_copier = PassengerCopier()
        passenger_serializer = PassengerSerializer()
        notifications_resetter = NotificationsResetter()
        task_submitter = TaskSubmitter()
        form_data_future = Future()
        distance_future = Future()
        fare_future = Future()
        passenger_id_future = Future()
        passenger_serialized_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                form_data_future.set(form.d)
                distance_calculator.\
                    perform(float(form.d.origin_latitude),
                            float(form.d.origin_longitude),
                            float(form.d.destination_latitude),
                            float(form.d.destination_longitude))

        class DistanceCalculatorSubscriber(object):
            def distance_calculated(self, distance):
                distance_future.set(distance)
                active_passenger_perks_getter.perform(perks_repository,
                                                      user.id)

        class ActivePassengerPerksGetterSubscriber(object):
            def active_passenger_perks_found(self, passenger_perks):
                fare_calculator.\
                    perform(passenger_perks[0].perk.fixed_rate,
                            passenger_perks[0].perk.multiplier,
                            int(params.seats),
                            distance_future.get())

        class FareCalculatorSubscriber(object):
            def fare_calculated(self, fare):
                fare_future.set(fare)
                credits_getter.perform(payments_repository, user.id)

        class CreditsGetterSubscriber(object):
            def credits_found(self, credits):
                credits_reserver.perform(payments_repository,
                                         credits,
                                         fare_future.get())

        class CreditsReserverSubscriber(object):
            def credits_not_found(self, credits):
                outer.publish('credits_not_found', credits)

            def payments_created(self, ignored):
                d = form_data_future.get()
                passenger_creator.perform(passengers_repository, user.id,
                                          d.origin,
                                          float(d.origin_latitude),
                                          float(d.origin_longitude),
                                          d.destination,
                                          float(d.destination_latitude),
                                          float(d.destination_longitude),
                                          distance_future.get(),
                                          int(d.seats),
                                          datetime_parser(d.pickup_time))

        class PassengerCreatorSubscriber(object):
            def passenger_created(self, passenger):
                passenger_id_future.set(passenger.id)
                orm.add(passenger)
                passenger_copier.perform(passengers_repository, passenger)

        class PassengerCopierSubscriber(object):
            def passenger_copied(self, passenger):
                passenger.user = user
                passenger_serializer.perform(passenger)

        class PassengerSerializerSubscriber(object):
            def passenger_serialized(self, passenger):
                passenger_serialized_future.set(passenger)
                notifications_resetter.perform(redis, user.id)

        class NotificationsResetterSubscriber(object):
            def notifications_reset(self, recordid):
                task_submitter.perform(task, passenger_serialized_future.get())

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success', passenger_id_future.get())

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        distance_calculator.add_subscriber(logger,
                                           DistanceCalculatorSubscriber())
        active_passenger_perks_getter.\
            add_subscriber(logger, ActivePassengerPerksGetterSubscriber())
        fare_calculator.add_subscriber(logger,
                                       FareCalculatorSubscriber())
        credits_getter.add_subscriber(logger,
                                      CreditsGetterSubscriber())
        credits_reserver.add_subscriber(logger,
                                        CreditsReserverSubscriber())
        passenger_creator.add_subscriber(logger, PassengerCreatorSubscriber())
        passenger_copier.add_subscriber(logger, PassengerCopierSubscriber())
        passenger_serializer.add_subscriber(logger,
                                            PassengerSerializerSubscriber())
        notifications_resetter.\
            add_subscriber(logger, NotificationsResetterSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        form_validator.perform(passengers_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))


class NotifyPassengersWorkflow(Publisher):
    """Defines a workflow to notify a passenger that a driver has offered
    a ride request.
    """

    def perform(self, logger, repository, passenger_ids, push_adapter, channel,
                payload_factory):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = MultiplePassengersWithIdGetter()
        payloads_creator = PayloadsByUserCreator()
        acs_ids_extractor = PassengersACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSPayloadsForUserIdNotifier()
        passengers_future = Future()
        payloads_future = Future()
        user_ids_future = Future()

        class PassengerGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_future.set(passengers)
                payloads_creator.perform(payload_factory,
                                         [p.user for p in passengers])

        class PayloadsCreatorSubscriber(object):
            def payloads_created(self, payloads):
                payloads_future.set(payloads)
                acs_ids_extractor.perform(passengers_future.get())

        class ACSUserIdExtractorSubscriber(object):
            def acs_user_ids_extracted(self, user_ids):
                user_ids_future.set(user_ids)
                acs_session_creator.perform(push_adapter)

        class ACSSessionCreatorSubscriber(object):
            def acs_session_not_created(self, error):
                outer.publish('failure', error)

            def acs_session_created(self, session_id):
                acs_notifier.perform(push_adapter, session_id, channel,
                                     zip(user_ids_future.get(),
                                         payloads_future.get()))

        class ACSNotifierSubscriber(object):
            def acs_user_ids_not_notified(self, error):
                outer.publish('failure', error)

            def acs_user_ids_notified(self):
                outer.publish('success')

        passengers_getter.add_subscriber(logger, PassengerGetterSubscriber())
        payloads_creator.add_subscriber(logger, PayloadsCreatorSubscriber())
        acs_ids_extractor.add_subscriber(logger,
                                         ACSUserIdExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
        passengers_getter.perform(repository, passenger_ids)


class DeactivatePassengerWorkflow(Publisher):
    """Defines a workflow to deactivate a passenger given its ID."""

    def perform(self, logger, orm, repository, passenger_id, user, task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = ActivePassengerWithIdGetter()
        with_user_id_authorizer = PassengerWithUserIdAuthorizer()
        passengers_deactivator = MultiplePassengersDeactivator()
        requests_cancellor = MultipleDriveRequestsCancellor()
        requests_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('success')

            def passenger_found(self, passenger):
                with_user_id_authorizer.perform(user.id, passenger)

        class WithUserIdAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')

            def authorized(self, user_id, passenger):
                passengers_deactivator.perform([passenger])

        class PassengersDeactivatorSubscriber(object):
            def passengers_hid(self, passengers):
                passenger = orm.merge(passengers[0])
                orm.add(passenger)
                requests_cancellor.perform(passenger.drive_requests)

        class DriveRequestsCancellorSubscriber(object):
            def drive_requests_cancelled(self, requests):
                orm.add_all(requests)
                requests_serializer.perform(requests)

        class DriveRequestSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        with_user_id_authorizer.\
            add_subscriber(logger, WithUserIdAuthorizerSubscriber())
        passengers_deactivator.\
            add_subscriber(logger, PassengersDeactivatorSubscriber())
        requests_cancellor.\
            add_subscriber(logger, DriveRequestsCancellorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        passenger_getter.perform(repository, passenger_id)


class AlightPassengerWorkflow(Publisher):
    """Defines a workflow to deactivate a passenger given its ID."""

    def perform(self, logger, gettext, orm, params, rate_repository,
                passenger_repository, perks_repository, payments_repository,
                passenger_id, user, task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        passenger_getter = PassengerWithIdGetter()
        with_user_id_authorizer = PassengerWithUserIdAuthorizer()
        passengers_deactivator = MultiplePassengersDeactivator()
        accepted_requests_filter = AcceptedDriveRequestsFilter()
        rate_creator = RateCreator()
        active_passenger_perks_getter = ActivePassengerPerksGetter()
        fare_calculator = FareCalculator()
        credits_getter = CreditsByUserIdGetter()
        fare_creator = FareCreator()
        active_driver_perks_getter = ActiveDriverPerksGetter()
        reimbursement_calculator = ReimbursementCalculator()
        reimbursement_creator = ReimbursementCreator()
        requests_deactivator = MultipleDriveRequestsDeactivator()
        requests_serializer = MultipleDriveRequestsSerializer()
        task_submitter = TaskSubmitter()
        stars_future = Future()
        requests_future = Future()
        fare_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                v = int(form.d.stars) if form.d.stars else 3
                stars_future.set(v)
                passenger_getter.perform(passenger_repository, passenger_id)

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('success')

            def passenger_found(self, passenger):
                with_user_id_authorizer.perform(user.id, passenger)

        class WithUserIdAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')

            def authorized(self, user_id, passenger):
                passengers_deactivator.perform([passenger])

        class PassengersDeactivatorSubscriber(object):
            def passengers_hid(self, passengers):
                passenger = orm.merge(passengers[0])
                orm.add(passenger)
                requests_future.set(passenger.drive_requests)
                accepted_requests_filter.perform(passenger.drive_requests)

        class AcceptedDriveRequestsFilterSubscriber(object):
            def drive_requests_extracted(self, requests):
                rate_creator.perform(rate_repository,
                                     requests[0].id,
                                     requests[0].passenger.user.id,
                                     requests[0].driver.user.id,
                                     False,
                                     stars_future.get())

        class RateCreatorSubscriber(object):
            def rate_created(self, rate):
                orm.add(rate)
                active_passenger_perks_getter.\
                    perform(perks_repository,
                            requests_future.get()[0].passenger.user.id)

        class ActivePassengerPerksGetterSubscriber(object):
            def active_passenger_perks_found(self, passenger_perks):
                requests = requests_future.get()
                fare_calculator.\
                    perform(passenger_perks[0].perk.fixed_rate,
                            passenger_perks[0].perk.multiplier,
                            requests[0].passenger.seats,
                            requests[0].passenger.distance)

        class FareCalculatorSubscriber(object):
            def fare_calculated(self, credits_):
                fare_future.set(credits_)
                credits_getter.perform(payments_repository, user.id)

        class CreditsGetterSubscriber(object):
            def credits_found(self, credits):
                requests = requests_future.get()
                fare_creator.perform(payments_repository,
                                     requests[0].id,
                                     requests[0].passenger.user.id,
                                     credits,
                                     fare_future.get())

        class FareCreatorSubscriber(object):
            def payments_created(self, payments):
                orm.add_all(payments)
                active_driver_perks_getter.\
                    perform(perks_repository,
                            requests_future.get()[0].driver.user.id)

        class ActiveDriverPerksGetterSubscriber(object):
            def active_driver_perks_found(self, driver_perks):
                requests = requests_future.get()
                reimbursement_calculator.\
                    perform(driver_perks[0].perk.fixed_rate,
                            driver_perks[0].perk.multiplier,
                            requests[0].passenger.seats,
                            requests[0].passenger.distance)

        class ReimbursementCalculatorSubscriber(object):
            def reimbursement_calculated(self, credits_):
                requests = requests_future.get()
                reimbursement_creator.perform(payments_repository,
                                              requests[0].id,
                                              requests[0].driver.user.id,
                                              credits_)

        class ReimbursementCreatorSubscriber(object):
            def payments_created(self, payments):
                orm.add_all(payments)
                requests_deactivator.perform(requests_future.get())

        class DriveRequestsDeactivatorSubscriber(object):
            def drive_requests_hid(self, requests):
                orm.add_all(requests)
                requests_serializer.perform(requests)

        class DriveRequestSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                task_submitter.perform(task, requests)

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        with_user_id_authorizer.\
            add_subscriber(logger, WithUserIdAuthorizerSubscriber())
        passengers_deactivator.\
            add_subscriber(logger, PassengersDeactivatorSubscriber())
        accepted_requests_filter.\
            add_subscriber(logger, AcceptedDriveRequestsFilterSubscriber())
        rate_creator.add_subscriber(logger, RateCreatorSubscriber())
        active_passenger_perks_getter.\
            add_subscriber(logger, ActivePassengerPerksGetterSubscriber())
        fare_calculator.\
            add_subscriber(logger, FareCalculatorSubscriber())
        credits_getter.add_subscriber(logger,
                                      CreditsGetterSubscriber())
        fare_creator.add_subscriber(logger, FareCreatorSubscriber())
        active_driver_perks_getter.\
            add_subscriber(logger, ActiveDriverPerksGetterSubscriber())
        reimbursement_calculator.\
            add_subscriber(logger, ReimbursementCalculatorSubscriber())
        reimbursement_creator.add_subscriber(logger,
                                             ReimbursementCreatorSubscriber())
        requests_deactivator.\
            add_subscriber(logger, DriveRequestsDeactivatorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        form_validator.perform(rates_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))


class DeactivateExpiredPassengersWorkflow(Publisher):
    """Defines a workflow to view the list of unmatched passengers."""

    def perform(self, logger, orm, expire_after, passengers_repository,
                notify_passengers_task, notify_drivers_task):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = ExpiredPassengersGetter()
        passengers_deactivator = MultiplePassengersDeactivator()
        passengers_serializer = MultiplePassengersSerializer()
        notify_passengers_submitter = TaskSubmitter()
        requests_deactivator = MultipleDriveRequestsDeactivator()
        requests_serializer = MultipleDriveRequestsSerializer()
        notify_drivers_submitter = TaskSubmitter()
        drive_requests_future = Future()

        class PassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                if not passengers:
                    outer.publish('success')
                else:
                    passengers_deactivator.perform(passengers)

        class PassengersDeactivatorSubscriber(object):
            def passengers_hid(self, passengers):
                merged_passengers = [orm.merge(p) for p in passengers]
                orm.add_all(merged_passengers)
                drive_requests = [
                    d for p in merged_passengers for d in p.drive_requests]
                drive_requests_future.set(drive_requests)
                passengers_serializer.perform(passengers)

        class PassengersSerializerSubscriber(object):
            def passengers_serialized(self, passengers):
                notify_passengers_submitter.perform(notify_passengers_task,
                                                    passengers)

        class NotifyPassengersSubscriber(object):
            def task_created(self, task_id):
                requests_deactivator.perform(drive_requests_future.get())

        class DriveRequestsDeactivatorSubscriber(object):
            def drive_requests_hid(self, requests):
                orm.add_all(requests)
                requests_serializer.perform(requests)

        class DriveRequestSerializerSubscriber(object):
            def drive_requests_serialized(self, requests):
                notify_drivers_submitter.perform(notify_drivers_task, requests)

        class NotifyDriversSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success')

        passengers_getter.add_subscriber(logger, PassengersGetterSubscriber())
        passengers_deactivator.\
            add_subscriber(logger, PassengersDeactivatorSubscriber())
        passengers_serializer.add_subscriber(logger,
                                             PassengersSerializerSubscriber())
        notify_passengers_submitter.\
            add_subscriber(logger, NotifyPassengersSubscriber())
        requests_deactivator.\
            add_subscriber(logger, DriveRequestsDeactivatorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        notify_drivers_submitter.add_subscriber(logger,
                                                NotifyDriversSubscriber())
        passengers_getter.perform(passengers_repository, expire_after)


class CalculateFareWorkflow(Publisher):
    def perform(self, gettext, logger, params, perks_repository, user):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        distance_calculator = DistanceCalculator()
        active_passenger_perks_getter = ActivePassengerPerksGetter()
        fare_calculator = FareCalculator()
        distance_future = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                distance_calculator.\
                    perform(float(form.d.origin_latitude),
                            float(form.d.origin_longitude),
                            float(form.d.destination_latitude),
                            float(form.d.destination_longitude))

        class DistanceCalculatorSubscriber(object):
            def distance_calculated(self, distance):
                distance_future.set(distance)
                active_passenger_perks_getter.perform(perks_repository,
                                                      user.id)

        class ActivePassengerPerksGetterSubscriber(object):
            def active_passenger_perks_found(self, passenger_perks):
                fare_calculator.\
                    perform(passenger_perks[0].perk.fixed_rate,
                            passenger_perks[0].perk.multiplier,
                            int(params.seats),
                            distance_future.get())

        class FareCalculatorSubscriber(object):
            def fare_calculated(self, credits_):
                outer.publish('success', credits_)

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        distance_calculator.add_subscriber(logger,
                                           DistanceCalculatorSubscriber())
        active_passenger_perks_getter.\
            add_subscriber(logger, ActivePassengerPerksGetterSubscriber())
        fare_calculator.add_subscriber(logger, FareCalculatorSubscriber())
        form_validator.perform(passengers_forms.calculate_fare(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))
