#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid as _uuid

import web
from sqlalchemy import create_engine as _create_engine
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Time
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base as _declarative_base



__all__ = ['create_engine', 'create_session', 'declarative_base', 'init_db',
           'uuid', 'Boolean', 'Column', 'DateTime', 'String', 'Text', 'Time']


def create_engine():
    '''Creates a new database engine.'''
    return _create_engine(web.config.DATABASE_URL, convert_unicode=True)


def create_session(engine=None):
    '''Creates a new database session.'''
    if engine is None:
        return create_session(create_engine())
    return scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))


def declarative_base():
    """Creates a new declarative base class.

    Wraps SQLAlchemy ``declarative_base`` by adding two new fields to the
    returned base class:  a ``session`` property and a ``query`` property handy
    to execute queries."""
    Session = create_session()
    Base = _declarative_base()
    Base.session = Session
    Base.query = Session.query_property()
    return Base


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import app.models
    app.models.Base.metadata.create_all(bind=create_engine())
    app.models.Base.session.commit()


def uuid():
    """Generates a ``uuid``."""
    return unicode(_uuid.uuid4())
