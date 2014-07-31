#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import required


add = form.Form(form.Textbox('telephone', required),
                form.Textbox('car_type'),
                form.Textbox('license_plate', required))
