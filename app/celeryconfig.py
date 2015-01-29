#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from celery.schedules import crontab


CELERY_IMPORTS = ('app.tasks',)

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERYBEAT_SCHEDULE = {
    'deactivate-expired-passengers': {
        'task': 'app.tasks.DeactivateExpiredPassengersTask',
        'schedule': crontab(minute='*/5')
    }
}

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

try:
    from local_celeryconfig import *
except ImportError:
    pass
