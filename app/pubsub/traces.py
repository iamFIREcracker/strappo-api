#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from collections import namedtuple

from app.weblib.pubsub import Publisher

ParsedTrace = namedtuple('ParsedTrace',
                         'app_version level date message'.split())


class TracesGetter(Publisher):
    def perform(self, repository, limit, offset):
        self.publish('traces_found', repository.all(limit, offset))


class MultipleTracesParser(Publisher):
    def perform(self, blob):
        self.publish('traces_parsed',
                     [ParsedTrace(o.get('app_version', ''),
                                  o['level'], o['date'], o['message'])
                      for o in json.loads(blob)])


class MultipleTracesCreator(Publisher):
    def perform(self, repository, user_id, traces):
        self.publish('traces_created',
                     [repository.add(user_id, t.app_version, t.level, t.date,
                                     t.message)
                      for t in traces])


def serialize(trace):
    if trace is None:
        return None
    return dict(id=trace.id,
                user_id=trace.user.id if trace.user else '',
                user_name=trace.user.name if trace.user else '',
                level=trace.level,
                date=trace.date,#.strftime('%Y-%m-%dT%H:%M:%SZ'),
                message=trace.message)


def _serialize(trace):
    d = serialize(trace)
    return d


class MultipleTracesSerializer(Publisher):
    def perform(self, traces):
        self.publish('traces_serialized',
                     [_serialize(t) for t in traces])


