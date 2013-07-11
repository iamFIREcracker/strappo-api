#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery.schedules import crontab

CELERY_IMPORTS = ('app.tasks',)

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERYBEAT_SCHEDULE = {
    'deactivate-passengers-every-morning': {
        'task': 'app.tasks.DeactivateActivePassengers',
        'schedule': crontab(hour=5, minute=0)
    },
    'deactivate-drive-requests-every-morning': {
        'task': 'app.tasks.DeactivateActiveDriveRequests',
        'schedule': crontab(hour=5, minute=5)
    },
    'unhide-hidden-drivers-every-morning': {
        'task': 'app.tasks.UnhideHiddenDrivers',
        'schedule': crontab(hour=5, minute=10)
    }
}
