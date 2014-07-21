#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import integer_optional


add = form.Form(form.Textbox('response_time', integer_optional))
