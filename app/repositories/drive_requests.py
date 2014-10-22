#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
from datetime import datetime

from app.models import Base
from app.models import Driver
from app.models import DriveRequest
from app.models import Passenger
from app.models import Rate
from app.models import User
from app.weblib.db import and_
from app.weblib.db import exists
from app.weblib.db import expunged
from app.weblib.db import func
from app.weblib.db import joinedload_all


class DriveRequestsRepository(object):
    @staticmethod
    def get_unrated_by_id(id, driver_id, user_id):
        options = [joinedload_all('driver.user'),
                   joinedload_all('passenger.user')]
        return expunged(DriveRequest.query.options(*options).\
                         filter(DriveRequest.driver_id == driver_id).\
                         filter(DriveRequest.accepted == True).\
                         filter(DriveRequest.cancelled == False).\
                         filter(DriveRequest.active == False).\
                         filter(Passenger.matched == True).\
                         filter(~exists().where(and_(Rate.drive_request_id == DriveRequest.id,
                                                      Rate.rater_user_id == user_id))).\
                        first(),
                        DriveRequest.session)

    @staticmethod
    def get_unrated_by_driver_id(driver_id, user_id):
        options = [joinedload_all('driver.user'),
                   joinedload_all('passenger.user')]
        return [expunged(dr, DriveRequest.session)
                for dr in DriveRequest.query.options(*options).\
                         filter(DriveRequest.driver_id == driver_id).\
                         filter(DriveRequest.accepted == True).\
                         filter(DriveRequest.cancelled == False).\
                         filter(DriveRequest.active == False).\
                         filter(Passenger.matched == True).\
                         filter(~exists().where(and_(Rate.drive_request_id == DriveRequest.id,
                                                      Rate.rater_user_id == user_id)))
                ]

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
    def add(driver_id, passenger_id, response_time=0):
        id = unicode(uuid.uuid4())
        drive_request = DriveRequest(id=id, driver_id=driver_id,
                                     passenger_id=passenger_id,
                                     accepted=False, cancelled=False,
                                     active=True, response_time=response_time,
                                     created=datetime.utcnow())
        return drive_request

    @staticmethod
    def cancel_by_driver_id(id, driver_id):
        request = expunged(DriveRequest.query.\
                                filter_by(id=id).\
                                filter_by(driver_id=driver_id).\
                                filter_by(active=True).first(),
                           DriveRequest.session)
        if request:
            request.active = False
            request.cancelled = True
        return request


    @staticmethod
    def cancel_by_passenger_id(id, passenger_id):
        request = expunged(DriveRequest.query.\
                                filter_by(id=id).\
                                filter_by(passenger_id=passenger_id).\
                                filter_by(active=True).first(),
                           DriveRequest.session)
        if request:
            request.active = False
            request.cancelled = True
        return request


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

    @staticmethod
    def rides_given(user_id):
        return Base.session.query(func.count()).\
            select_from(DriveRequest).\
            join('driver', 'user').\
            filter(User.id == user_id).\
            filter(DriveRequest.accepted == True).\
            first()[0]

    @staticmethod
    def distance_driven(user_id):
        return Base.session.query(func.coalesce(func.sum(Passenger.distance),
                                                0.0)).\
            select_from(DriveRequest).\
            join('driver', 'user').\
            join('passenger').\
            filter(User.id == user_id).\
            filter(DriveRequest.accepted == True).\
            first()[0]
