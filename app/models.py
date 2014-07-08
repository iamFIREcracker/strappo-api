#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from app.weblib.db import backref
from app.weblib.db import func
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



Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'

    session_id = Column(String, primary_key=True)
    atime = Column(Time, default=datetime.utcnow)
    data = Column(Text)


class User(Base):
    __tablename__ = 'user'

    id = Column(String, default=uuid, primary_key=True)
    acs_id = Column(String) # XXX This field shouldn't be nullable;  if it is,
                            # it is just because I am too lazy to fix all the
                            # tests.
    name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    email = Column(String, nullable=True)
    locale = Column(String, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    driver = relationship('Driver', uselist=False,
                          backref=backref('user', cascade='expunge'),
                             primaryjoin="and_(User.id == Driver.user_id,"
                                              "Driver.active == True)")
    passenger = relationship('Passenger', uselist=False,
                             backref=backref('user', cascade='expunge'),
                             primaryjoin="and_(User.id == Passenger.user_id,"
                                              "Passenger.active == True)")
    @property
    def stars(self):
        return Base.session.query(func.sum(Rate.stars)/func.count(Rate.id)).\
                filter(Rate.rated_user_id == self.id).first()[0]

    @property
    def rates(self):
        return Base.session.query(func.count(Rate.id)).\
                filter(Rate.rated_user_id == self.id).first()[0]


    def __repr__(self):
        data = u'<User id=%(id)s, acs_id=%(acs_id)s, name=%(name)s, '\
                'avatar=%(avatar)s, email=%(email)s, '\
                'locale=%(locale)s>' % self.__dict__
        return data.encode('utf-8')


class Token(Base):
    __tablename__ = 'token'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    def __repr__(self):
        data = u'<Token id=%(id)s, user_id=%(user_id)s>' % self.__dict__
        return data.encode('utf-8')


class Driver(Base):
    __tablename__ = 'driver'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    license_plate = Column(String)
    telephone = Column(String)
    hidden = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    drive_requests = relationship('DriveRequest', uselist=True,
                                  backref=backref('driver', cascade='expunge'),
                                  primaryjoin="and_(Driver.id == DriveRequest.driver_id,"
                                                   "DriveRequest.active == True)")

    def __repr__(self):
        data = u'<Driver id=%(id)s, user_id=%(user_id)s, '\
                'license_plate=%(license_plate)s, '\
                'telephone=%(telephone)s, hidden=%(hidden)s, '\
                'active=%(active)s>' % self.__dict__
        return data.encode('utf-8')


class Passenger(Base):
    __tablename__ = 'passenger'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    origin = Column(Text)
    origin_latitude = Column(Float)
    origin_longitude = Column(Float)
    destination = Column(Text)
    destination_latitude = Column(Float)
    destination_longitude = Column(Float)
    seats = Column(Integer)
    matched = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)
    drive_requests = relationship('DriveRequest', uselist=True,
                                  backref=backref('passenger', cascade='expunge'),
                                  primaryjoin="and_(Passenger.id == DriveRequest.passenger_id,"
                                                   "DriveRequest.active == True)")

    def __repr__(self):
        data = u'<Passenger id=%(id)s, user_id=%(user_id)s, '\
               'origin=%(origin)s, origin_latitude=%(origin_latitude)s, '\
               'origin_longitude=%(origin_longitude)s, '\
               'destination=%(destination)s, destination_latitude=%(destination_latitude)s, '\
               'destination_longitude=%(destination_longitude)s, '\
               'seats=%(seats)d, matched=%(matched)s,  active=%(active)s>' % self.__dict__
        return data.encode('utf-8')


class DriveRequest(Base):
    __tablename__ = 'drive_request'

    id = Column(String, default=uuid, primary_key=True)
    driver_id = Column(String, ForeignKey('driver.id'))
    passenger_id = Column(String, ForeignKey('passenger.id'))
    accepted = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    response_time = Column(Integer, nullable=False, server_default=text('0'))
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    def __repr__(self):
        data = u'<DriveRequest id=%(id)s, driver_id=%(driver_id)s, '\
                'passenger_id=%(passenger_id)s, '\
                'accepted=%(accepted)s, active=%(active)s, '\
                'response_time=%(response_time)s>' % self.__dict__
        return data.encode('utf-8')


class Trace(Base):
    __tablename__ = 'trace'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    level = Column(String)
    date = Column(String)
    message = Column(Text)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    def __repr__(self):
        data = u'<Trace id=%(id)s, user_id=%(user_id)s, '\
                'level=%(level)s, date=%(date)s, '\
                'message=%(message)s>' % self.__dict__
        return data.encode('utf-8')


class Rate(Base):
    __tablename__ = 'rate'

    id = Column(String, default=uuid, primary_key=True)
    rater_user_id = Column(String, ForeignKey('user.id'))
    rated_user_id = Column(String, ForeignKey('user.id'))
    stars = Column(Integer, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow,
                     onupdate=datetime.utcnow)

    def __repr__(self):
        data = u'<Rating id=%(id)s, rater_user_id=%(rater_user_id)s, '\
                'rated_user_id=%(rated_user_id)s, '\
                'stars=%(stars)s>' % self.__dict__
        return data.encode('utf-8')
