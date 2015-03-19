#!/usr/bin/env python
# -*- coding: utf-8 -*-

from strappon.pubsub.poi import ActivePOIExtractor
from strappon.pubsub.poi import POISerializer
from weblib.pubsub import LoggingSubscriber
from weblib.pubsub import Publisher


class ListActivePOIWorkflow(Publisher):
    def perform(self, logger, poi):
        outer = self  # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        active_poi_extractor = ActivePOIExtractor()
        poi_serializer = POISerializer()

        class POIExtractorSubscriber(object):
            def poi_extracted(self, poi):
                poi_serializer.perform(poi)

        class POISerializerSubscriber(object):
            def poi_serialized(self, poi):
                outer.publish('success', poi)

        active_poi_extractor.add_subscriber(logger, POIExtractorSubscriber())
        poi_serializer.add_subscriber(logger, POISerializerSubscriber())
        active_poi_extractor.perform(poi)
