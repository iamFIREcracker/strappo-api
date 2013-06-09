#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import ActiveDriver
from app.models import User
from app.models import Driver
from app.weblib.db import expunged


class DriversRepository(object):
    @staticmethod
    def get(driver_id):
        return expunged(Driver.query.join(ActiveDriver).join(User).\
                                filter(Driver.id == driver_id).\
                                filter(User.deleted == False).first(),
                        Driver.session)

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
