#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from app.weblib.db import Boolean
from app.weblib.db import declarative_base
from app.weblib.db import relationship
from app.weblib.db import uuid
from app.weblib.db import Boolean
from app.weblib.db import Column
from app.weblib.db import DateTime
from app.weblib.db import Float
from app.weblib.db import ForeignKey
from app.weblib.db import Integer
from app.weblib.db import String
from app.weblib.db import Text
from app.weblib.db import Time
from app.weblib.db import text
from app.weblib.db import ReprMixin


Base = declarative_base()


class User(Base, ReprMixin):
    __tablename__ = 'user'

    id = Column(String, default=uuid, primary_key=True)
    acs_id = Column(String)  # XXX Should be not nullable
    facebook_id = Column(String)  # XXX Should be not nullable
    name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    email = Column(String, nullable=True)
    locale = Column(String, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    active_driver = relationship('Driver', uselist=False, cascade='expunge',
                                 primaryjoin=""
                                 "and_(User.id == Driver.user_id,"
                                 "Driver.active == True)")
    active_passenger = \
        relationship('Passenger', uselist=False, cascade='expunge',
                     primaryjoin=""
                     "and_(User.id == Passenger.user_id,"
                     "Passenger.active == True)")


class Token(Base, ReprMixin):
    __tablename__ = 'token'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)


class Driver(Base, ReprMixin):
    __tablename__ = 'driver'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    car_make = Column(String)
    car_model = Column(String)
    car_color = Column(String)
    license_plate = Column(String)
    telephone = Column(String)
    hidden = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    user = relationship('User', uselist=False, cascade='expunge')
    drive_requests = \
        relationship('DriveRequest', uselist=True, cascade='expunge',
                     primaryjoin=""
                     "and_(Driver.id == DriveRequest.driver_id,"
                     "DriveRequest.active == True)")


class Passenger(Base, ReprMixin):
    __tablename__ = 'passenger'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    origin = Column(Text)
    origin_latitude = Column(Float)
    origin_longitude = Column(Float)
    destination = Column(Text)
    destination_latitude = Column(Float)
    destination_longitude = Column(Float)
    distance = Column(Float, nullable=False, server_default=text('0'))
    seats = Column(Integer)
    matched = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    user = relationship('User', uselist=False, cascade='expunge')
    drive_requests = \
        relationship('DriveRequest', uselist=True, cascade='expunge',
                     primaryjoin=""
                     "and_(Passenger.id == DriveRequest.passenger_id,"
                     "DriveRequest.active == True)")


class DriveRequest(Base, ReprMixin):
    __tablename__ = 'drive_request'

    id = Column(String, default=uuid, primary_key=True)
    driver_id = Column(String, ForeignKey('driver.id'))
    passenger_id = Column(String, ForeignKey('passenger.id'))
    accepted = Column(Boolean, default=False)
    cancelled = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    response_time = Column(Integer, nullable=False, server_default=text('0'))
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    driver = relationship('Driver', uselist=False, cascade='expunge')
    passenger = relationship('Passenger', uselist=False, cascade='expunge')


class Rate(Base, ReprMixin):
    __tablename__ = 'rate'

    id = Column(String, default=uuid, primary_key=True)
    drive_request_id = Column(String, ForeignKey('drive_request.id'),
                              nullable=False)
    rater_user_id = Column(String, ForeignKey('user.id'), nullable=False)
    rated_user_id = Column(String, ForeignKey('user.id'), nullable=False)
    rater_is_driver = Column(Boolean, nullable=False)
    stars = Column(Integer, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)


class DriverPerk(Base, ReprMixin):
    __tablename__ = 'driver_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    name = Column(String, nullable=False)
    eligible_for = Column(Integer, nullable=False)
    active_for = Column(Integer, nullable=False)
    fixed_rate = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False)


class EligibleDriverPerk(Base, ReprMixin):
    __tablename__ = 'eligible_driver_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    user_id = Column(String, ForeignKey('user.id'), nullable=True)
    perk_id = Column(String, ForeignKey('driver_perk.id'), nullable=True)
    valid_until = Column(DateTime, nullable=False)

    perk = relationship('DriverPerk', uselist=False, cascade='expunge')


class ActiveDriverPerk(Base, ReprMixin):
    __tablename__ = 'active_driver_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    user_id = Column(String, ForeignKey('user.id'), nullable=True)
    perk_id = Column(String, ForeignKey('driver_perk.id'), nullable=True)
    valid_until = Column(DateTime, nullable=False)

    perk = relationship('DriverPerk', uselist=False, cascade='expunge')


class PassengerPerk(Base, ReprMixin):
    __tablename__ = 'passenger_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    name = Column(String, nullable=False)
    eligible_for = Column(Integer, nullable=False)
    active_for = Column(Integer, nullable=False)
    fixed_rate = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False)


class EligiblePassengerPerk(Base, ReprMixin):
    __tablename__ = 'eligible_passenger_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    user_id = Column(String, ForeignKey('user.id'), nullable=True)
    perk_id = Column(String, ForeignKey('passenger_perk.id'), nullable=True)
    valid_until = Column(DateTime, nullable=False)

    perk = relationship('PassengerPerk', uselist=False, cascade='expunge')


class ActivePassengerPerk(Base, ReprMixin):
    __tablename__ = 'active_passenger_perk'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    user_id = Column(String, ForeignKey('user.id'), nullable=True)
    perk_id = Column(String, ForeignKey('passenger_perk.id'), nullable=True)
    valid_until = Column(DateTime, nullable=False)

    perk = relationship('PassengerPerk', uselist=False, cascade='expunge')


class Payment(Base, ReprMixin):
    __tablename__ = 'payment'

    id = Column(String, default=uuid, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    drive_request_id = Column(String, ForeignKey('drive_request.id'),
                              nullable=True)
    payer_user_id = Column(String, ForeignKey('user.id'), nullable=True)
    payee_user_id = Column(String, ForeignKey('user.id'), nullable=True)
    credits = Column(Integer, nullable=False)


class Trace(Base, ReprMixin):
    __tablename__ = 'trace'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    app_version = Column(String)
    level = Column(String)
    date = Column(String)
    message = Column(Text)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    user = relationship('User', uselist=False)


class Feedback(Base, ReprMixin):
    __tablename__ = 'feedback'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    message = Column(Text)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    user = relationship('User', uselist=False)
