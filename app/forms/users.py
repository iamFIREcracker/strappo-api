#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form


__all__ = ['add']


validurl = form.Validator('Should be a valid URL.',
                          lambda v: v.startswith('http://'))


add = form.Form(form.Textbox('name', form.notnull, description='Name',
                             placeholder='John Smith'),
                form.Textbox('avatar', validurl, description='Avatar',
                             placeholder='http://...'))
