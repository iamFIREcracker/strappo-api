#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime as dt

from web import form


required = form.Validator('required', bool)
integer = form.Validator('integer_required', bool)


def datetime_parser(v):
    return dt.strptime(v, '%Y-%m-%dT%H:%M:%SZ')


def datetime_validator(v):
    return datetime_parser(v)


datetime = form.Validator('datetime', datetime_validator)


def datetime_optional_parser(v):
    if v is None:
        return v
    return datetime_parser(v)


def datetime_optional_validator(v):
    return datetime_optional_parser(v)


datetime_optional = form.Validator('datetime_optional',
                                   datetime_optional_validator)


stars = form.Validator('integer_optional_between_0_and_5',
                       lambda v: not v or 0 < int(v) <= 5)
