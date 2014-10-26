#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Trace
from app.weblib.db import expunged
from app.weblib.db import func
from app.weblib.db import joinedload_all


class TracesRepository(object):
    @staticmethod
    def all(limit, offset):
        options = [joinedload_all('user')]
        return [expunged(t, Trace.session)
                for t in Trace.query.options(*options).\
                         order_by(Trace.date.desc()).\
                         limit(limit).\
                         offset(offset)
                ]

    @staticmethod
    def add(user_id, app_version, level, date, message):
        id = unicode(uuid.uuid4())
        trace = Trace(id=id, user_id=user_id, app_version=app_version,
                      level=level, date=date, message=message)
        return trace
