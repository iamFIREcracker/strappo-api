#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from . import config


def get_name():
    """Gets the name of the application."""
    return config.APP_NAME


def get_version():
    """Gets the repository version."""
    import subprocess
    proc = subprocess.Popen(
            'hg log -r tip --template "{latesttagdistance}"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pending, _ = proc.communicate()
    return "%(tag)sd%(pending)s" % dict(tag=config.TAG, pending=pending)


def app_factory():
    """App factory."""
    import web

    web.config.debug = config.debug
    web.config.debug_sql = config.debug_sql

    web.config.DEV = config.DEV

    web.config.LOGGER_NAME = config.LOGGER_NAME
    web.config.LOG_ENABLE = config.LOG_ENABLE
    web.config.LOG_FORMAT = config.LOG_FORMAT

    web.config.DATABASE_URL = config.DATABASE_URL


    from app.database import create_session
    from app.logging import create_logger
    from app.tools.app_processors import load_logger
    from app.tools.app_processors import load_path_url
    from app.tools.app_processors import load_render
    from app.tools.app_processors import load_session
    from app.tools.app_processors import load_sqla
    from app.urls import URLS

    views = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views')
    app = web.application(URLS, globals())
    dbpath = web.config.DATABASE_URL.replace('sqlite:///', '')
    db = web.database(dbn='sqlite', db=dbpath)
    session = web.session.Session(app, web.session.DBStore(db, 'session'))

    app.add_processor(web.loadhook(load_path_url))
    app.add_processor(web.loadhook(load_logger(lambda:
                                               create_logger(web.config))))
    app.add_processor(web.loadhook(load_render(views)))
    app.add_processor(web.loadhook(load_session(session)))
    app.add_processor(load_sqla(create_session()))

    return app
