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

    def test_get_with_invalid_id_should_return_nothing(self):
        # When
        driver = DriversRepository.get('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_get_with_id_linked_to_deleted_user_should_return_nothing(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()

        # When
        driver = DriversRepository.get('did')

        # Then
        self.assertIsNone(driver)

    def test_get_with_id_linked_to_active_user_should_return_the_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()

        # When
        driver = DriversRepository.get('did')

        # Then
        self.assertIsNotNone(driver)

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

    def test_get_using_id_of_active_user_should_the_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()

        # When
        driver = DriversRepository.with_user_id('uid')

        # Then
        self.assertIsNotNone(driver)

    def test_update_of_not_existing_driver_should_return_nothing(self):
        # When
        driver = DriversRepository.update('not_existing_id', 'license', 'phone')

        # Then
        self.assertIsNone(driver)

    def test_update_of_existing_driver_should_return_the_updated_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        self.session.add(DriversRepository.update('did', 'license', 'phone'))
        self.session.commit()
        driver = Driver.query.filter_by(id='did').first()

        # Then
        self.assertEquals('license', driver.license_plate)
        self.assertEquals('phone', driver.telephone)

    def test_hide_of_not_existing_driver_should_return_nothing(self):
        # When
        driver = DriversRepository.hide('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_hide_of_existing_driver_should_return_the_hided_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        self.session.add(DriversRepository.hide('did'))
        self.session.commit()
        driver = Driver.query.filter_by(id='did').first()

        # Then
        self.assertEquals(False, driver.active)

    def test_unhide_of_not_existing_driver_should_return_nothing(self):
        # When
        driver = DriversRepository.unhide('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_unhide_of_existing_driver_should_return_the_hided_driver(self):
        # Given
        self.session.begin(subtransactions=True)
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate',
                                hidden=True))
        self.session.commit()

        # When
        self.session.begin(subtransactions=True)
        self.session.add(DriversRepository.unhide('did'))
        self.session.commit()
        driver = Driver.query.filter_by(id='did').first()

        # Then
        self.assertEquals(True, driver.active)
