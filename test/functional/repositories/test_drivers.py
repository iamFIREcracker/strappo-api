#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from app.models import Driver
from app.models import User
from app.repositories.drivers import DriversRepository


class TestDriversRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize the database
        from app.weblib.db import init_db
        init_db()

        cls.session = Driver.session
        cls.query = Driver.query

    def setUp(self):
        Driver.session.begin(subtransactions=True)

    def tearDown(self):
        Driver.session.rollback()
        Driver.session.remove()

    def test_get_using_invalid_user_id_should_return_nothing(self):
        # When
        driver = DriversRepository.with_user_id('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_get_using_id_of_deleted_user_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()

        # When
        driver = DriversRepository.with_user_id('uid')

        # Then
        self.assertIsNone(driver)

    def test_get_using_id_of_active_user_should_the_associated_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()

        # When
        driver = DriversRepository.with_user_id('uid')

        # Then
        self.assertEquals('plate', driver.license_plate)
