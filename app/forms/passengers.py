#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form


__all__ = ['add']


validint = form.Validator('Should be an integer', int)


add = form.Form(form.Textbox('origin', form.notnull, description='Origin'),
                form.Textbox('destination', form.notnull,
                             description='Destination'),
                form.Textbox('seats', form.notnull, description='Buddies'))
