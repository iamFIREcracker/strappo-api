#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Rate


class RatesRepository(object):
    @staticmethod
    def add(rater_user_id, rated_user_id, stars):
        id = unicode(uuid.uuid4())
        rate = Rate(id=id,
                    rater_user_id=rater_user_id,
                    rated_user_id=rated_user_id,
                    stars=stars)
        return rate
