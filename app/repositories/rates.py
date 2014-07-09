#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Base
from app.models import Rate
from app.weblib.db import func



class RatesRepository(object):
    @staticmethod
    def add(rater_user_id, rated_user_id, stars):
        id = unicode(uuid.uuid4())
        rate = Rate(id=id,
                    rater_user_id=rater_user_id,
                    rated_user_id=rated_user_id,
                    stars=stars)
        return rate

    @staticmethod
    def avg_stars(rated_user_id):
        return Base.session.query(func.avg(Rate.stars)).\
                filter(Rate.rated_user_id == rated_user_id).first()[0]

    @staticmethod
    def received_rates(rated_user_id):
        return Base.session.query(func.count(Rate.id)).\
                filter(Rate.rated_user_id == rated_user_id).first()[0]

