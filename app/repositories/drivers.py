#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import User
from app.models import Driver
from app.weblib.db import expunged
from app.weblib.db import joinedload
from app.weblib.db import joinedload_all


class DriversRepository(object):
    @staticmethod
    def get(driver_id):
        return expunged(Driver.query.options(joinedload('user')).\
                                filter(User.deleted == False).\
                                filter(Driver.id == driver_id).\
                                first(),
                        Driver.session)

    @staticmethod
    def get_active_by_id(driver_id):
        return expunged(Driver.query.options(joinedload('user')).\
                        filter(User.deleted == False).\
                        filter(Driver.id == driver_id).\
                        filter(Driver.active == True).\
                        first(),
                        Driver.session)

    @staticmethod
    def get_with_requests(driver_id):
        return expunged(Driver.query.options(joinedload('user'),
                                             joinedload_all('drive_requests.driver.user'),
                                             joinedload_all('drive_requests.passenger.user')).\
                                filter(Driver.id == driver_id).\
                                filter(User.deleted == False).first(),
                        Driver.session)

    @staticmethod
    def get_all_unhidden():
        return [expunged(d, Driver.session)
                for d in Driver.query.options(joinedload('user')).\
                                filter(User.deleted == False).\
                                filter(Driver.hidden == False).\
                                filter(Driver.active == True)]

    @staticmethod
    def get_all_hidden():
        return [expunged(d, Driver.session)
                for d in Driver.query.options(joinedload('user')).\
                                filter(User.deleted == False).\
                                filter(Driver.hidden == True)]

    @staticmethod
    def with_user_id(user_id):
        return expunged(Driver.query.options(joinedload('user')).\
                                filter(User.id == user_id).\
                                filter(User.deleted == False).first(),
                        Driver.session)

    @staticmethod
    def add(user_id, car_make, car_model, car_color, license_plate, telephone):
        id = unicode(uuid.uuid4())
        driver = Driver(id=id, user_id=user_id, car_make=car_make,
                        car_model=car_model, car_color=car_color,
                        license_plate=license_plate, telephone=telephone,
                        hidden=False, active=True)
        return driver


    @staticmethod
    def unhide(driver_id):
        driver = DriversRepository.get(driver_id)
        if driver is None:
            return None
        else:
            driver.hidden = False
            return driver
