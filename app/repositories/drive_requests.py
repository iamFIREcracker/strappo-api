#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import DriveRequest
from app.weblib.db import expunged


class DriveRequestsRepository(object):
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
