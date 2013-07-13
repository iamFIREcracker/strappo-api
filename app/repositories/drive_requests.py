#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import User
from app.models import DriveRequest
from app.weblib.db import expunged
from app.weblib.db import joinedload_all


class DriveRequestsRepository(object):
    @staticmethod
    def get_all_active():
        return [expunged(dr, DriveRequest.session)
                for dr in DriveRequest.query.\
                        filter(User.deleted == False).\
                        filter(DriveRequest.active == True)]

    @staticmethod
    def get_all_active_by_driver(driver_id):
        options = [joinedload_all('driver.user'),
                   joinedload_all('passenger.user')]
        return [expunged(dr, DriveRequest.session)
                for dr in DriveRequest.query.options(*options).\
                        filter(User.deleted == False).\
                        filter(DriveRequest.driver_id == driver_id).\
                        filter(DriveRequest.active == True)]

    @staticmethod
    def get_all_active_by_passenger(passenger_id):
        options = [joinedload_all('driver.user'),
                   joinedload_all('passenger.user')]
        return [expunged(dr, DriveRequest.session)
                for dr in DriveRequest.query.options(*options).\
                        filter(User.deleted == False).\
                        filter(DriveRequest.passenger_id == passenger_id).\
                        filter(DriveRequest.active == True)]

    @staticmethod
    def add(driver_id, passenger_id):
        id = unicode(uuid.uuid4())
        drive_request = DriveRequest(id=id, driver_id=driver_id,
                                   passenger_id=passenger_id,
                                   accepted=False, active=True)
        return drive_request

    @staticmethod
    def accept(driver_id, passenger_id):
        request = expunged(DriveRequest.query.\
                                filter_by(driver_id=driver_id).\
                                filter_by(passenger_id=passenger_id).\
                                filter_by(accepted=False).\
                                filter_by(active=True).first(),
                           DriveRequest.session)
        if request:
            request.accepted = True
        return request
