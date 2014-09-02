#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import required


add = form.Form(form.Textbox('telephone', required),
                form.Textbox('car_make'),
                form.Textbox('car_model'),
                form.Textbox('car_color', required),
                form.Textbox('license_plate', required))
