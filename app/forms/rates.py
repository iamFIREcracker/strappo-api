#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

from app.forms import stars


add = form.Form(form.Textbox('stars', stars))
