#!/usr/bin/env python
# -*- coding: utf-8 -*-


import app.forms.passengers as passengers_forms
from app.pubsub.passengers import AllPassengersGetter
from app.pubsub.passengers import PassengerWithIdGetter
from app.pubsub.passengers import MultiplePassengersSerializer
from app.pubsub.passengers import PassengerCreator
from app.pubsub.passengers import PassengerSerializer
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import LoggingSubscriber


class PassengersWorkflow(Publisher):
    """Defines a workflow to view the list of active passengers."""

    def perform(self, logger, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = AllPassengersGetter()
        passengers_serializer = MultiplePassengersSerializer()

        class AllPassengersGetterSubscriber(object):
            def passengers_found(self, passengers):
                passengers_serializer.perform(passengers)

        class PassengersSerializerSubscriber(object):
            def passengers_serialized(self, blob):
                outer.publish('success', blob)


        passengers_getter.add_subscriber(logger,
                                         AllPassengersGetterSubscriber())
        passengers_serializer.add_subscriber(logger,
                                             PassengersSerializerSubscriber())
        passengers_getter.perform(repository)


class AddPassengerWorkflow(Publisher):
    """Defines a workflow to add a new passenger."""

    def perform(self, orm, logger, params, repository, user_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        passenger_creator = PassengerCreator()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)
            def valid_form(self, form):
                passenger_creator.perform(repository, user_id, form.d.origin,
                                          form.d.destination,
                                          int(form.d.buddies))

        class PassengerCreatorSubscriber(object):
            def passenger_created(self, passenger):
                orm.add(passenger)
                outer.publish('success', passenger.id)

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        passenger_creator.add_subscriber(logger, PassengerCreatorSubscriber())
        form_validator.perform(passengers_forms.add(), params,
                               describe_invalid_form)


class ViewPassengerWorkflow(Publisher):
    """Defines a workflow to view the details of an active passenger."""

    def perform(self, logger, repository, passenger_id):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        passengers_getter = PassengerWithIdGetter()
        passenger_serializer = PassengerSerializer()

        class AllPassengersGetterSubscriber(object):
            def passenger_not_found(self, passenger_id):
                outer.publish('not_found', passenger_id)
            def passenger_found(self, passenger):
                passenger_serializer.perform(passenger)

        class PassengersSerializerSubscriber(object):
            def passenger_serialized(self, blob):
                outer.publish('success', blob)


        passengers_getter.add_subscriber(logger,
                                         AllPassengersGetterSubscriber())
        passenger_serializer.add_subscriber(logger,
                                            PassengersSerializerSubscriber())
        passengers_getter.perform(repository, passenger_id)
