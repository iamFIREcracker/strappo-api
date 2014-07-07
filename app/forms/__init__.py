#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form

required = form.Validator('required', bool)
integer = form.Validator('integer_required', bool)
integer_optional = form.Validator('integer_optional',
                                  lambda v: not v or int(v) >= 0)
