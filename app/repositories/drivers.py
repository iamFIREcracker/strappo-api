#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import ActiveDriver
from app.models import User
from app.models import Driver


class DriversRepository(object):

    @staticmethod
    def get(driver_id):
        driver = Driver.query.join(ActiveDriver).join(User).\
                filter(Driver.id == driver_id).\
                filter(User.deleted == False).first()
        if driver is None:
            return None
        Driver.session.expunge(driver)
        return driver

    @staticmethod
    def with_user_id(user_id):
        return Driver.query.join(ActiveDriver).join(User).\
                filter(User.id == user_id).\
                filter(User.deleted == False).first()

    @staticmethod
    def update(driver_id, license_plate, telephone):
        driver = DriversRepository.get(driver_id)
        if driver is None:
            return None
        else:
            driver.license_plate = license_plate
            driver.telephone = telephone
            return driver
