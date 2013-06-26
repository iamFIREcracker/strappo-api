#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import User
from app.models import Driver
from app.weblib.db import expunged

from app.weblib.db import joinedload


class DriversRepository(object):
    @staticmethod
    def get(driver_id):
        return expunged(Driver.query.join(User).\
                                filter(Driver.id == driver_id).\
                                filter(User.deleted == False).first(),
                        Driver.session)

    @staticmethod
    def get_all_unhidden():
        return [expunged(d, Driver.session)
                for d in Driver.query.options(joinedload('user.device')).\
                                join(User).\
                                filter(User.deleted == False).\
                                filter(Driver.hidden == False)]

    @staticmethod
    def with_user_id(user_id):
        return Driver.query.join(User).\
                filter(User.id == user_id).\
                filter(User.deleted == False).first()

    @staticmethod
    def add(user_id, license_plate, telephone):
        id = unicode(uuid.uuid4())
        driver = Driver(id=id, user_id=user_id, license_plate=license_plate,
                        telephone=telephone, hidden=False)
        return driver


    @staticmethod
    def update(driver_id, license_plate, telephone):
        driver = DriversRepository.get(driver_id)
        if driver is None:
            return None
        else:
            driver.license_plate = license_plate
            driver.telephone = telephone
            return driver

    @staticmethod
    def hide(driver_id):
        driver = DriversRepository.get(driver_id)
        if driver is None:
            return None
        else:
            driver.hidden = True
            return driver

    @staticmethod
    def unhide(driver_id):
        driver = DriversRepository.get(driver_id)
        if driver is None:
            return None
        else:
            driver.hidden = False
            return driver
