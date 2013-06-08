#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from weblib.db import declarative_base
from weblib.db import uuid
from weblib.db import Boolean
from weblib.db import Column
from weblib.db import DateTime
from weblib.db import Enum
from weblib.db import ForeignKey
from weblib.db import Integer
from weblib.db import String
from weblib.db import Text
from weblib.db import Time



Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'

    session_id = Column(String, primary_key=True)
    atime = Column(Time, default=datetime.now)
    data = Column(Text)


class User(Base):
    __tablename__ = 'user'

    id = Column(String, default=uuid, primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<User id=%(id)s, name=%(name)s, '\
               'avatar=%(avatar)s>' % self.__dict__


class Account(Base):
    __tablename__ = 'account'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    external_id = Column(String, nullable=False)
    type = Column(Enum('fake', 'facebook', name='account_type'), nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<Account id=%(id)s, user_id=%(user_id)s, '\
               'external_id=%(external_id)s, type=%(type)s>' % self.__dict__


class Token(Base):
    __tablename__ = 'token'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<Token id=%(id)s, user_id=%(user_id)s>' % self.__dict__


class Driver(Base):
    __tablename__ = 'driver'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    license_plate = Column(String)
    telephone = Column(String)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<Driver id=%(id)s, user_id=%(user_id)s, '\
               'license_plate=%(license_plate)s, '\
               'telephone=%(telephone)s>' % self.__dict__


class ActiveDriver(Base):
    __tablename__ = 'active_driver'

    id = Column(String, default=uuid, primary_key=True)
    driver_id = Column(String, ForeignKey('driver.id'))
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Passenger(Base):
    __tablename__ = 'passenger'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    origin = Column(Text)
    destination = Column(Text)
    buddies = Column(Integer)
