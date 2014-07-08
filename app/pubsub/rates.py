#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class RateCreator(Publisher):
    def perform(self, repository, rater_user_id, rated_user_id, stars):
        rate = repository.add(rater_user_id, rated_user_id, stars)
        self.publish('rate_created', rate)
