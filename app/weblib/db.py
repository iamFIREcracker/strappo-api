#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid as _uuid

import web
from sqlalchemy import and_
from sqlalchemy import create_engine as _create_engine
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Time
from sqlalchemy import text
from sqlalchemy.orm import backref
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base as _declarative_base



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


def clear_db():
    import contextlib
    import app.models
    engine = create_engine()
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        for table in reversed(app.models.Base.metadata.sorted_tables):
            con.execute(table.delete())
        trans.commit()

def uuid():
    """Generates a ``uuid``."""
    return unicode(_uuid.uuid4())


def expunged(obj, session):
    """Expunges the given object from session.

    A simple wrapper of ``session.expunge()`` enabling user to pass in None
    object reference.  This comes in handy with methods doing query on the
    database ed returning the result to the user.
    """
    if obj is None:
        return None
    session.expunge(obj)
    return obj


# Credits to
# https://bitbucket.org/shadytrees/brownstone/src/tip/brownstone/sqlalchemy.py
class ReprMixin(object):
    """Hooks into SQLAlchemy's magic to make :meth:`__repr__`s."""
    def __repr__(self):
        def reprs():
            for col in self.__table__.c:
                yield col.name, repr(getattr(self, col.name))

        def format(seq):
            for key, value in seq:
                yield '%s=%s' % (key, value)

        args = '(%s)' % ', '.join(format(reprs()))
        classy = type(self).__name__
        return classy + args
