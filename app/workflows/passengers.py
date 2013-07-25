#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.passengers as passengers_forms
from app.pubsub import ACSSessionCreator
from app.pubsub import ACSUserIdsNotifier
from app.pubsub.passengers import ActivePassengersGetter
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import MultiplePassengersDeactivator
from app.pubsub.passengers import MultiplePassengersSerializer
from app.pubsub.passengers import PassengerACSUserIdExtractor
from app.pubsub.passengers import PassengerCreator
from app.pubsub.passengers import PassengerSerializer
from app.pubsub.passengers import PassengerWithUserIdAuthorizer
from app.pubsub.passengers import PassengerLinkedToDriverWithUserIdAuthorizer
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import TaskSubmitter
from app.weblib.pubsub import Future


class ActivePassengersWorkflow(Publisher):
    """Defines a workflow to view the list of active passengers."""

    def perform(self, logger, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = ActivePassengersGetter()
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

    def perform(self, orm, logger, params, repository, user_id, task):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        passenger_creator = PassengerCreator()
        task_submitter = TaskSubmitter()
        passenger_id = Future()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                passenger_creator.perform(repository, user_id, form.d.origin,
                                          form.d.destination,
                                          int(form.d.seats))

        class PassengerCreatorSubscriber(object):
            def passenger_created(self, passenger):
                orm.add(passenger)
                passenger_id.set(passenger.id)
                task_submitter.perform(task, passenger_id.get())

        class TaskSubmitterSubscriber(object):
            def task_created(self, task_id):
                outer.publish('success', passenger_id.get())

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        passenger_creator.add_subscriber(logger, PassengerCreatorSubscriber())
        task_submitter.add_subscriber(logger, TaskSubmitterSubscriber())
        form_validator.perform(passengers_forms.add(), params,
                               describe_invalid_form)


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


class NotifyPassengerWorkflow(Publisher):
    """Defines a workflow to notify a passenger that a driver has offered 
    a ride request.
    """

    def perform(self, logger, repository, passenger_id, push_adapter, channel,
                payload):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passenger_getter = PassengerWithIdGetter()
        acs_id_extractor = PassengerACSUserIdExtractor()
        acs_session_creator = ACSSessionCreator()
        acs_notifier = ACSUserIdsNotifier()
        user_ids_future = Future()

        class PassengerGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('passenger_not_found', passenger_id)
            def passenger_found(self, passenger):
                acs_id_extractor.perform(passenger)

        class ACSUserIdExtractorSubscriber(object):
            def acs_user_id_extracted(self, user_id):
                user_ids_future.set([user_id])
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

        passenger_getter.add_subscriber(logger, PassengerGetterSubscriber())
        acs_id_extractor.add_subscriber(logger,
                                        ACSUserIdExtractorSubscriber())
        acs_session_creator.add_subscriber(logger,
                                           ACSSessionCreatorSubscriber())
        acs_notifier.add_subscriber(logger, ACSNotifierSubscriber())
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
