#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import RideRequest


class RideRequestsRepository(object):
    @staticmethod
    def add(driver_id, passenger_id):
        id = unicode(uuid.uuid4())
        ride_request = RideRequest(id=id, driver_id=driver_id,
                                   passenger_id=passenger_id,
                                   accepted=False)
        return ride_request
