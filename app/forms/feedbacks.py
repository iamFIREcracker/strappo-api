#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import required


add = form.Form(form.Textbox('message', required))
