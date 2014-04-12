#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.passengers as passengers_forms
from app.pubsub import ACSSessionCreator
from app.pubsub import ACSPayloadsForUserIdNotifier
from app.pubsub import PayloadsByUserCreator
from app.pubsub.drive_requests import AcceptedDriveRequestsFilter
from app.pubsub.drive_requests import DriveRequestCancellorByDriverId
from app.pubsub.drive_requests import MultipleDriveRequestsDeactivator
from app.pubsub.drive_requests import MultipleDriveRequestsSerializer
from app.pubsub.notifications import NotificationsResetter
from app.pubsub.passengers import ActivePassengersGetter
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import MultiplePassengersWithIdGetter
from app.pubsub.passengers import MultiplePassengersDeactivator
from app.pubsub.passengers import MultiplePassengersSerializer
from app.pubsub.passengers import PassengersACSUserIdExtractor
from app.pubsub.passengers import PassengerCreator
from app.pubsub.passengers import PassengerCopier
from app.pubsub.passengers import PassengerUpdater
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import PassengerSerializer
from app.pubsub.passengers import PassengerWithUserIdAuthorizer
from app.pubsub.passengers import PassengerLinkedToDriverWithUserIdAuthorizer
from app.pubsub.passengers import UnmatchedPassengersGetter
from app.pubsub.users import UserWithoutPassengerValidator
from app.weblib.forms import describe_invalid_form
from app.weblib.forms import describe_invalid_form_localized
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import TaskSubmitter
from app.weblib.pubsub import Future


class ListUnmatchedPassengersWorkflow(Publisher):
    """Defines a workflow to view the list of unmatched passengers."""

    def perform(self, logger, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = UnmatchedPassengersGetter()
        passengers_serializer = MultiplePassengersSerializer()

        class ActivePassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_serializer.perform(passengers)

        class PassengersSerializerSubscriber(object):
            def passengers_serialized(self, blob):
                outer.publish('success', blob)


        passengers_getter.add_subscriber(logger,
                                         ActivePassengersGetterSubscriber())
        passengers_serializer.add_subscriber(logger,
                                             PassengersSerializerSubscriber())
        passengers_getter.perform(repository)


class AddPassengerWorkflow(Publisher):
    """Defines a workflow to add a new passenger."""

    def perform(self, gettext, orm, logger, redis, params,
                repository, user, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_validator = UserWithoutPassengerValidator()
        form_validator = FormValidator()
        passenger_getter = PassengerWithIdGetter()
        passenger_creator = PassengerCreator()
        passenger_updater = PassengerUpdater()
        passenger_copier = PassengerCopier()
        passenger_serializer = PassengerSerializer()
        notifications_resetter = NotificationsResetter()
        task_submitter = TaskSubmitter()
        passenger_future = Future()
        passenger_id_future = Future()
        passenger_serialized_future = Future()

        class UserValidatorSubscriber(object):
            def invalid_user(self, errors):
                passenger_getter.perform(repository, user.passenger.id)
            def valid_user(self, user):
                passenger_future.set(None)
                form_validator.perform(passengers_forms.add(), params,
                                       describe_invalid_form_localized(gettext,
                                                                       user.locale))

        class PassengerGetterSubscriber(object):
            def passenger_found(self, passenger):
                passenger_future.set(passenger)
                form_validator.perform(passengers_forms.add(), params,
                                       describe_invalid_form_localized(gettext,
                                                                       user.locale))

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                passenger = passenger_future.get()
                if passenger is None:
                    passenger_creator.perform(repository, user.id,
                                              form.d.origin,
                                              form.d.destination,
                                              int(form.d.seats))
                else:
                    passenger_updater.perform(passenger,
                                              form.d.origin,
                                              form.d.destination,
                                              int(form.d.seats))

        class PassengerCreatorSubscriber(object):
            def passenger_created(self, passenger):
                passenger_id_future.set(passenger.id)
                orm.add(passenger)
                passenger_copier.perform(repository, passenger)

        class PassengerUpdaterSubscriber(object):
            def passenger_updated(self, passenger):
                passenger_id_future.set(passenger.id)
                orm.add(passenger)
                passenger_copier.perform(repository, passenger)

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

        user_validator.add_subscriber(logger, UserValidatorSubscriber())
        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        passenger_creator.add_subscriber(logger, PassengerCreatorSubscriber())
        passenger_updater.add_subscriber(logger, PassengerUpdaterSubscriber())
        passenger_copier.add_subscriber(logger, PassengerCopierSubscriber())
        passenger_serializer.add_subscriber(logger,
                                            PassengerSerializerSubscriber())
        notifications_resetter.\
                add_subscriber(logger, NotificationsResetterSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        user_validator.perform(user)


class ViewPassengerWorkflow(Publisher):
    """Defines a workflow to view the details of an active passenger."""

    def perform(self, logger, repository, passenger_id, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = PassengerWithIdGetter()
        with_user_id_authorizer = PassengerWithUserIdAuthorizer()
        linked_to_driver_authorizer = \
                PassengerLinkedToDriverWithUserIdAuthorizer()
        passenger_serializer = PassengerSerializer()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found', passenger_id)
            def passenger_found(self, passenger):
                with_user_id_authorizer.perform(user_id, passenger)

        class WithUserIdAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                linked_to_driver_authorizer.perform(user_id, passenger)
            def authorized(self, user_id, passenger):
                passenger_serializer.perform(passenger)

        class LinkedToDriverAuthorizerSubscriber(object):
            def unauthorized(self, user_id, passenger):
                outer.publish('unauthorized')
            def authorized(self, user_id, passenger):
                passenger_serializer.perform(passenger)

        class PassengersSerializerSubscriber(object):
            def passenger_serialized(self, blob):
                outer.publish('success', blob)

        passengers_getter.add_subscriber(logger, PassengerGetterSubscriber())
        with_user_id_authorizer.add_subscriber(logger,
                                               WithUserIdAuthorizerSubscriber())
        linked_to_driver_authorizer.\
                add_subscriber(logger, LinkedToDriverAuthorizerSubscriber())
        passenger_serializer.add_subscriber(logger,
                                            PassengersSerializerSubscriber())
        passengers_getter.perform(repository, passenger_id)


class NotifyPassengersWorkflow(Publisher):
    """Defines a workflow to notify a passenger that a driver has offered 
    a ride request.
    """

    def perform(self, logger, repository, passenger_ids, push_adapter, channel,
                payload_factory):
        outer = self # Handy to access ``self`` from inner classes
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
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = PassengerWithIdGetter()
        with_user_id_authorizer = PassengerWithUserIdAuthorizer()
        passengers_deactivator = MultiplePassengersDeactivator()
        requests_deactivator = MultipleDriveRequestsDeactivator()
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
                orm.add(passengers[0])
                requests_deactivator.perform(passengers[0].drive_requests)

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

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        with_user_id_authorizer.\
                add_subscriber(logger, WithUserIdAuthorizerSubscriber())
        passengers_deactivator.add_subscriber(logger,
                                              PassengersDeactivatorSubscriber())
        requests_deactivator.\
                add_subscriber(logger, DriveRequestsDeactivatorSubscriber())
        requests_serializer.add_subscriber(logger,
                                           DriveRequestSerializerSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        passenger_getter.perform(repository, passenger_id)


class DeactivateActivePassengersWorkflow(Publisher):
    """Defines a workflow to deactivate all the active passengers."""

    def perform(self, logger, orm, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = ActivePassengersGetter()
        passengers_deactivator = MultiplePassengersDeactivator()

        class ActivePassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_deactivator.perform(passengers)

        class PassengersDeactivatorSubscriber(object):
            def passengers_hid(self, passengers):
                orm.add_all(passengers)
                outer.publish('success', passengers)

        passengers_getter.add_subscriber(logger,
                                         ActivePassengersGetterSubscriber())
        passengers_deactivator.add_subscriber(logger,
                                              PassengersDeactivatorSubscriber())
        passengers_getter.perform(repository)
