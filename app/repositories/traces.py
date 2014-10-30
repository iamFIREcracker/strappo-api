#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Trace


class TracesRepository(object):
    @staticmethod
    def add(user_id, app_version, level, date, message):
        id = unicode(uuid.uuid4())
        trace = Trace(id=id, user_id=user_id, app_version=app_version,
                      level=level, date=date, message=message)
        return trace
