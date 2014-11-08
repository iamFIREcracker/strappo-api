#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.traces import MultipleTracesCreator
from strappon.pubsub.traces import MultipleTracesParser

from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher


class AddTracesWorkflow(Publisher):
    def perform(self, orm, logger, user_id, repository, blob):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        traces_parser = MultipleTracesParser()
        traces_creator = MultipleTracesCreator()

        class TracesParserSubscriber(object):
            def traces_parsed(self, traces):
                traces_creator.perform(repository, user_id, traces)

        class TracesCreatorSubscriber(object):
            def traces_created(self, traces):
                orm.add_all(traces)
                outer.publish('success')

        traces_parser.add_subscriber(logger, TracesParserSubscriber())
        traces_creator.add_subscriber(logger, TracesCreatorSubscriber())
        traces_parser.perform(blob)
