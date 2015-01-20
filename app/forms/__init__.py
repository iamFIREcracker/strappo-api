#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from web import form


required = form.Validator('required', bool)
integer = form.Validator('integer_required', bool)
integer_optional = form.Validator('integer_optional',
                                  lambda v: not v or int(v))


def time_parser(v):
    return datetime.strptime(v, '%H:%M').time()


def time_validator(v):
    return time_parser(v)


time = form.Validator('time_required', time_validator)


stars = form.Validator('integer_optional_between_0_and_5',
                       lambda v: not v or 0 < int(v) <= 5)
