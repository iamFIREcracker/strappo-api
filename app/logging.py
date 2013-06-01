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

from logging import getLogger, StreamHandler, Formatter, getLoggerClass, DEBUG


def create_logger(config):
    """Creates a logger for the given application. This logger works
similar to a regular Python logger but changes the effective logging
level based on the application's debug flag. Furthermore this
function also removes all attached handlers in case there was a
logger with the log name before.
"""
    Logger = getLoggerClass()

    class DebugLogger(Logger):
        def getEffectiveLevel(x):
            if x.level == 0 and config.debug:
                return DEBUG
            return Logger.getEffectiveLevel(x)

    class DebugHandler(StreamHandler):
        def emit(x, record):
            StreamHandler.emit(x, record) if config.debug else None

    handler = DebugHandler()
    handler.setLevel(DEBUG)
    handler.setFormatter(Formatter(config.LOG_FORMAT))
    logger = getLogger(config.LOGGER_NAME)
    # just in case that was not a new logger, get rid of all the handlers
    # already attached to it.
    del logger.handlers[:]
    logger.__class__ = DebugLogger
    if config.LOG_ENABLE:
        logger.addHandler(handler)
    return logger
