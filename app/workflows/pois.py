#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.pois import ActivePOISExtractor
from strappon.pubsub.pois import POISSerializer
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher


class ListActivePOISWorkflow(Publisher):
    def perform(self, logger, pois):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        active_pois_extractor = ActivePOISExtractor()
        pois_serializer = POISSerializer()

        class POISExtractorSubscriber(object):
            def pois_extracted(self, pois):
                pois_serializer.perform(pois)

        class POISSerializerSubscriber(object):
            def pois_serialized(self, pois):
                outer.publish('success', pois)

        active_pois_extractor.add_subscriber(logger, POISExtractorSubscriber())
        pois_serializer.add_subscriber(logger, POISSerializerSubscriber())
        active_pois_extractor.perform(pois)
