#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import datetime


add = form.Form(form.Textbox('offered_pickup_time', datetime))
