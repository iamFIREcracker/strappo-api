#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import RideRequest
from app.weblib.db import expunged


class RideRequestsRepository(object):
    @staticmethod
    def add(driver_id, passenger_id):
        id = unicode(uuid.uuid4())
        ride_request = RideRequest(id=id, driver_id=driver_id,
                                   passenger_id=passenger_id,
                                   accepted=False)
        return ride_request

    @staticmethod
    def accept(driver_id, passenger_id):
        request = expunged(RideRequest.query.\
                                filter_by(driver_id=driver_id).\
                                filter_by(passenger_id=passenger_id).\
                                filter_by(accepted=False).first(),
                           RideRequest.session)
        if request:
            request.accepted = True
        return request
