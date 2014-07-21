#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Base
from app.models import Rate
from app.weblib.db import func



class RatesRepository(object):
    @staticmethod
    def add(drive_request_id, rater_user_id, rated_user_id, rater_is_driver,
            stars):
        id = unicode(uuid.uuid4())
        rate = Rate(id=id,
                    drive_request_id=drive_request_id,
                    rater_user_id=rater_user_id,
                    rated_user_id=rated_user_id,
                    rater_is_driver=rater_is_driver,
                    stars=stars)
        return rate

    @staticmethod
    def avg_stars(rated_user_id):
        avg = Base.session.query(func.avg(Rate.stars)).\
                filter(Rate.rated_user_id == rated_user_id).first()[0]
        return 0.0 if avg is None else avg

    @staticmethod
    def received_rates(rated_user_id):
        return Base.session.query(func.count()).\
                filter(Rate.rated_user_id == rated_user_id).first()[0]

