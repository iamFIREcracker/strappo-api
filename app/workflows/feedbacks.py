#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.feedbacks import FeedbackCreator
from weblib.forms import describe_invalid_form_localized
from weblib.pubsub import FormValidator
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher

import app.forms.feedbacks as feedbacks_forms


class AddFeedbackWorkflow(Publisher):
    def perform(self, gettext, orm, logger, feedbacks_repository,
                user, params):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        form_validator = FormValidator()
        feedback_creator = FeedbackCreator()

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form', errors)

            def valid_form(self, form):
                feedback_creator.perform(feedbacks_repository,
                                         user.id, form.d.message)

        class FeedbackCreatorSubscriber(object):
            def feedback_created(self, feedback):
                orm.add(feedback)
                outer.publish('success')

        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        feedback_creator.add_subscriber(logger, FeedbackCreatorSubscriber())
        form_validator.perform(feedbacks_forms.add(), params,
                               describe_invalid_form_localized(gettext,
                                                               user.locale))
