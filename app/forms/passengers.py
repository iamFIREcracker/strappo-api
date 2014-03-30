#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import integer
from app.forms import required


add = form.Form(form.Textbox('origin', required),
                form.Textbox('destination', required),
                form.Textbox('seats', integer))
