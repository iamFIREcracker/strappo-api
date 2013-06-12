#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.models import Passenger
from app.models import User
from app.weblib.db import func


class DestinationsRepository(object):
    @staticmethod
    def get_all():
        return list(Passenger.session.query(Passenger.destination,
                                       func.count().label('rating')).distinct().\
                        join(User).filter(User.deleted == False).\
                        group_by(Passenger.destination).order_by('rating DESC'))
