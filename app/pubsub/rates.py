#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class RateCreator(Publisher):
    def perform(self, repository, drive_request_id, rater_user_id,
                rated_user_id, rater_is_driver, stars):
        rate = repository.add(drive_request_id, rater_user_id, rated_user_id,
                              rater_is_driver, stars)
        self.publish('rate_created', rate)
