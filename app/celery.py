#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from celery import Celery


celery = Celery('app.celery')
celery.config_from_object('celeryconfig')
