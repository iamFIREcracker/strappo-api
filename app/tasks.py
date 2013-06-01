#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.celery import celery


@celery.task
def add(x, y):
    return x + y
