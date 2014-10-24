#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class FeedbackCreator(Publisher):
    def perform(self, repository, user_id, message):
        self.publish('feedback_created', repository.add(user_id, message))
