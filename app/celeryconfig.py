#!/usr/bin/env python
# -*- coding: utf-8 -*-


CELERY_IMPORTS = ('app.tasks',)

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

try:
    from local_celeryconfig import *
except ImportError:
    pass
