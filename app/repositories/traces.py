#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Trace
from app.weblib.db import expunged
from app.weblib.db import func
from app.weblib.db import joinedload_all


class TracesRepository(object):
    @staticmethod
    def all():
        options = [joinedload_all('user')]
        return [expunged(t, Trace.session)
                for t in Trace.query.options(*options).\
                         #filter(DriveRequest.accepted == True).\
                         order_by(Trace.user_id,
                                  Trace.created.desc())
                ]

    @staticmethod
    def add(user_id, level, date, message):
        id = unicode(uuid.uuid4())
        trace = Trace(id=id, user_id=user_id, level=level, date=date,
                      message=message)
        return trace
