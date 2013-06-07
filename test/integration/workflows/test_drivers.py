#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from web.utils import storage

from mock import MagicMock
from mock import Mock

from app.workflows.drivers import ViewDriverWorkflow


class TestViewDriverWorkflow(unittest.TestCase):
    
    def test_not_found_is_published_if_invoked_with_invalid_driver_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=None))
        subscriber = Mock(not_found=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id')

        # Then
        subscriber.not_found.assert_called_with('not_existing_id')

    def test_serialized_driver_is_published_if_invoked_with_existing_driver_id(self):
        # Given
        logger = Mock()
        repository = Mock(get=MagicMock(return_value=storage(id='did',
                                                             user_id='uid',
                                                             license_plate='1242124',
                                                             telephone='+124 453534')))
        subscriber = Mock(driver_view=MagicMock())
        instance = ViewDriverWorkflow()

        # When
        instance.add_subscriber(subscriber)
        instance.perform(logger, repository, 'not_existing_id')

        # Then
        subscriber.driver_view.assert_called_with({
            'id': 'did',
            'user_id': 'uid',
            'license_plate': '1242124',
            'telephone': '+124 453534',
            'active': None
        })

