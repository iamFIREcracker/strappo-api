#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from collections import namedtuple

from app.weblib.pubsub import Publisher

ParsedTrace = namedtuple('ParsedTrace',
                         'app_version level date message'.split())


class MultipleTracesParser(Publisher):
    def perform(self, blob):
        self.publish('traces_parsed',
                     [ParsedTrace(o.get('app_version', None),
                                  o['level'], o['date'], o['message'])
                      for o in json.loads(blob)])


class MultipleTracesCreator(Publisher):
    def perform(self, repository, user_id, traces):
        self.publish('traces_created',
                     [repository.add(user_id, t.app_version, t.level, t.date,
                                     t.message)
                      for t in traces])
