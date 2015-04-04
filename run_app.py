#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app import app_factory
from weblib.logging import create_logger


app = app_factory()


def internalerror():
    message = '''
Holy shit!\n
method: %(method)s
fullpath: %(fullpath)s
env: %(env)s
''' % dict(method=web.ctx.method,
           fullpath=web.ctx.fullpath,
           env=web.ctx.environ
           )
    create_logger().exception(message)
    raise web.internalerror('Holy shit!')
app.internalerror = internalerror

if __name__ == '__main__':
    app.run()
