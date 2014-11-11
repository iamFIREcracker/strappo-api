#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app import app_factory
from weblib.logging import create_logger


app = app_factory()


def internalerror():
    create_logger().exception('Holy shit!')
    raise web.internalerror('Holy shit!')
app.internalerror = internalerror

if __name__ == '__main__':
    app.run()
