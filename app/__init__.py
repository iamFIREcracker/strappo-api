#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import web

from . import config


web.config.debug = web.config.DEBUG = config.DEBUG
web.config.debug_sql = web.config.DEBUG_SQL = config.DEBUG_SQL

web.config.DEV = config.DEV

web.config.LOGGER_NAME = config.LOGGER_NAME
web.config.LOG_ENABLE = config.LOG_ENABLE
web.config.LOG_FORMAT = config.LOG_FORMAT

web.config.DATABASE_URL = config.DATABASE_URL

web.config.DISABLE_HTTP_ACCEPT_CHECK = config.DISABLE_HTTP_ACCEPT_CHECK

web.config.TITANIUM_KEY = config.TITANIUM_KEY


def app_factory():
    """App factory."""
    import weblib.db
    from app.urls import URLS
    from app.weblib.app_processors import load_logger
    from app.weblib.app_processors import load_path_url
    from app.weblib.app_processors import load_render
    from app.weblib.app_processors import load_session
    from app.weblib.app_processors import load_and_manage_orm

    views = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views')
    app = web.application(URLS, globals())
    dbpath = web.config.DATABASE_URL.replace('sqlite:///', '')
    db = web.database(dbn='sqlite', db=dbpath)
    session = web.session.Session(app, web.session.DBStore(db, 'session'))

    app.add_processor(web.loadhook(load_logger))
    app.add_processor(web.loadhook(load_path_url))
    app.add_processor(web.loadhook(load_render(views)))
    app.add_processor(web.loadhook(load_session(session)))
    app.add_processor(load_and_manage_orm(weblib.db.create_session()))

    return app
