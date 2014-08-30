#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher

from app.pubsub.traces import MultipleTracesCreator
from app.pubsub.traces import MultipleTracesParser
from app.pubsub.traces import TracesGetter
from app.pubsub.traces import MultipleTracesSerializer


class ListTracesWorkflow(Publisher):
    def perform(self, logger, repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        traces_getter = TracesGetter()
        traces_serializer = MultipleTracesSerializer()

        class TracesGetterSubscriber(object):
            def traces_found(self, traces):
                traces_serializer.perform(traces)

        class TracesSerializerSusbcriber(object):
            def traces_serialized(self, traces):
                outer.publish('success', traces)

        traces_getter.add_subscriber(logger, TracesGetterSubscriber())
        traces_serializer.add_subscriber(logger, TracesSerializerSusbcriber())
        traces_getter.perform(repository)


class AddTracesWorkflow(Publisher):
    def perform(self, orm, logger, user_id, repository, blob):
        outer = self # Handy to access ``self`` from inner classes
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
