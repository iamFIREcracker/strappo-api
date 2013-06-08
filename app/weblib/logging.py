#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
flask.logging
~~~~~~~~~~~~~

Implements the logging support for Flask.

:copyright: (c) 2011 by Armin Ronacher.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import web

from logging import getLogger
from logging import getLoggerClass
from logging import DEBUG
from logging import Formatter
from logging import INFO
from logging import StreamHandler


__all__ = ['create_logger']


def create_logger():
    """Creates a logger for the given application.
    
    This logger works similar to a regular Python logger but changes the
    effective logging level based on the application's debug flag.  Furthermore
    this function also removes all attached handlers in case there was a logger
    with the log name before.
    """
    Logger = getLoggerClass()

    class DebugLogger(Logger):
        def getEffectiveLevel(self):
            if self.level == 0:
                return DEBUG if web.config.DEBUG else INFO
            return super(DebugLogger, self).getEffectiveLevel()

    class DebugHandler(StreamHandler):
        def emit(x, record):
            StreamHandler.emit(x, record)

    handler = DebugHandler()
    handler.setLevel(DEBUG)
    handler.setFormatter(Formatter(web.config.LOG_FORMAT))
    logger = getLogger(web.config.LOGGER_NAME)
    # just in case that was not a new logger, get rid of all the handlers
    # already attached to it.
    del logger.handlers[:]
    logger.__class__ = DebugLogger
    if web.config.LOG_ENABLE:
        logger.addHandler(handler)
    return logger
