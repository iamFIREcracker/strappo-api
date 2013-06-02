#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from weblib.db import declarative_base
from weblib.db import uuid
from weblib.db import Boolean
from weblib.db import Column
from weblib.db import DateTime
from weblib.db import ForeignKey
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
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class Token(Base):
    __tablename__ = 'token'

    id = Column(String, default=uuid, primary_key=True)
    user_id = Column(String, ForeignKey('user.id'))
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
