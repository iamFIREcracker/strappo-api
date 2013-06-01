#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import MagicMock
from mock import Mock

from app.workflows.users import add_user


class TestAddUserWorkflow(unittest.TestCase):

    def test_cannot_add_user_without_specifying_name(self):
        # Given
        logger = Mock()
        params = dict(phone='+2354 325345', avatar='http://avatar.com/me.png')

        # When
        ok, ret = add_user(logger, params, None)

        # Then
        self.assertFalse(ok)
        self.assertFalse(ret['success'])
        self.assertIn('name', ret['errors'])

    def test_cannot_add_user_without_specifying_phone(self):
        # Given
        logger = Mock()
        params = dict(name='John Smith', avatar='http://avatar.com/me.png')

        # When
        ok, ret = add_user(logger, params, None)

        # Then
        self.assertFalse(ok)
        self.assertFalse(ret['success'])
        self.assertIn('phone', ret['errors'])

    def test_cannot_add_user_with_invalid_avatar(self):
        # Given
        logger = Mock()
        params = dict(name='John Smith', phone='+2354 325345',
                      avatar='file://avatar.com/me.png')

        # When
        ok, ret = add_user(logger, params, None)

        # Then
        self.assertFalse(ok)
        self.assertFalse(ret['success'])
        self.assertIn('avatar', ret['errors'])

    def test_can_add_new_user(self):
        # Given
        logger = Mock()
        params = dict(name='John Smith', phone='+2354 325345',
                      avatar='http://avatar.com/me.png')
        repository = Mock(update=MagicMock(return_value=True))

        # When
        ok, _ = add_user(logger, params, repository)

        # Then
        self.assertTrue(ok)


