#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import integer
from app.forms import required


add = form.Form(form.Textbox('origin', required),
                form.Textbox('origin_latitude', required),
                form.Textbox('origin_longitude', required),
                form.Textbox('destination', required),
                form.Textbox('destination_latitude', required),
                form.Textbox('destination_longitude', required),
                form.Textbox('seats', integer))

calculate_fare = form.Form(form.Textbox('origin_latitude', required),
                           form.Textbox('origin_longitude', required),
                           form.Textbox('destination_latitude', required),
                           form.Textbox('destination_longitude', required),
                           form.Textbox('seats', integer))
