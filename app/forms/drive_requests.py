#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import datetime_validator


add = form.Form(form.Textbox('offered_pickup_time', datetime_validator))
