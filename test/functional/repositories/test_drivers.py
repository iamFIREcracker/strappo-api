#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import app.weblib.db
from app.models import Base
from app.models import Driver
from app.models import User
from app.repositories.drivers import DriversRepository


class TestDriversRepository(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        app.weblib.db.init_db()

    def setUp(self):
        app.weblib.db.clear_db()
        self.session = Base.session
        self.query = Driver.query

    def tearDown(self):
        self.session.remove()

    def test_get_all_unhidden_drivers_should_not_return_deleted_users(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_unhidden()

        # Then
        self.assertEquals([], drivers)

    def test_get_all_unhidden_drivers_should_not_return_hidden_drivers(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Driver(id='did', user_id='uid', hidden=True))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_unhidden()

        # Then
        self.assertEquals([], drivers)

    def test_get_all_unhidden_drivers(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Driver(id='did', user_id='uid', hidden=False))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_unhidden()

        # Then
        self.assertEquals(1, len(drivers))
        self.assertEquals('did', drivers[0].id)

    def test_get_all_hidden_drivers_should_not_return_deleted_users(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_hidden()

        # Then
        self.assertEquals([], drivers)

    def test_get_all_hidden_drivers_should_not_return_unhidden_drivers(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Driver(id='did', user_id='uid', hidden=False))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_hidden()

        # Then
        self.assertEquals([], drivers)

    def test_get_all_hidden_drivers(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=False))
        self.session.add(Driver(id='did', user_id='uid', hidden=True))
        self.session.commit()
        self.session.remove()

        # When
        drivers = DriversRepository.get_all_hidden()

        # Then
        self.assertEquals(1, len(drivers))
        self.assertEquals('did', drivers[0].id)

    def test_get_with_invalid_id_should_return_nothing(self):
        # When
        driver = DriversRepository.get('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_get_with_id_linked_to_deleted_user_should_return_nothing(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        driver = DriversRepository.get('did')

        # Then
        self.assertIsNone(driver)

    def test_get_with_id_linked_to_active_user_should_return_the_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()
        self.session.remove()

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
        self.session.add(User(id='uid', name='Name', avatar='Avatar',
                              deleted=True))
        self.session.add(Driver(id='did', user_id='uid'))
        self.session.commit()
        self.session.remove()

        # When
        driver = DriversRepository.with_user_id('uid')

        # Then
        self.assertIsNone(driver)

    def test_get_using_id_of_active_user_should_the_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()
        self.session.remove()

        # When
        driver = DriversRepository.with_user_id('uid')

        # Then
        self.assertIsNotNone(driver)

    def test_add_driver_with_all_the_valid_fields_should_return_a_new_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.commit()
        self.session.remove()

        # When
        driver = DriversRepository.add('uid', 'license', 'phone')
        self.session.add(driver)
        self.session.commit()
        driver = self.query.filter_by(id=driver.id).first()

        # Then
        self.assertEquals('license', driver.license_plate)

    def test_update_of_not_existing_driver_should_return_nothing(self):
        # When
        driver = DriversRepository.update('not_existing_id', 'license', 'phone')

        # Then
        self.assertIsNone(driver)

    def test_update_of_existing_driver_should_return_the_updated_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()
        self.session.remove()

        # When
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

    def test_hide_of_existing_driver_should_return_the_hid_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate'))
        self.session.commit()
        self.session.remove()

        # When
        self.session.add(DriversRepository.hide('did'))
        self.session.commit()
        driver = Driver.query.filter_by(id='did').first()

        # Then
        self.assertEquals(True, driver.hidden)

    def test_unhide_of_not_existing_driver_should_return_nothing(self):
        # When
        driver = DriversRepository.unhide('not_existing_id')

        # Then
        self.assertIsNone(driver)

    def test_unhide_of_existing_driver_should_return_the_hid_driver(self):
        # Given
        self.session.add(User(id='uid', name='Name', avatar='Avatar'))
        self.session.add(Driver(id='did', user_id='uid', license_plate='plate',
                                hidden=True))
        self.session.commit()
        self.session.remove()

        # When
        self.session.add(DriversRepository.unhide('did'))
        self.session.commit()
        driver = Driver.query.filter_by(id='did').first()

        # Then
        self.assertEquals(False, driver.hidden)
