#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from webassets import Bundle
from webassets import Environment


env = Environment('./static', '/static')
env.debug = web.debug

## Register your budles here!
#env.register('base_css',
#             Bundle("bootstrap/css/bootstrap.min.css",
#                    "bootstrap/css/bootstrap-responsive.min.css",
#                    "bootstrap-datepicker/css/datepicker.css",
#                    "bootstrap-fileupload/css/bootstrap-fileupload.min.css",
#                    "css/main.css"))
