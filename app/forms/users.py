#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form


__all__ = ['add']


validurl = form.Validator('Should be a valid URL.',
                          lambda v: v.startswith('http://') or
                          v.startswith('https://'))


add = form.Form(form.Hidden('acs_id', form.notnull),
                form.Hidden('facebook_id', form.notnull),
                form.Textbox('first_name', form.notnull),
                form.Textbox('last_name', form.notnull),
                form.Textbox('name', form.notnull),
                form.Textbox('avatar_unresolved', validurl),
                form.Textbox('avatar', validurl),
                form.Textbox('email', form.notnull),
                form.Textbox('locale', form.notnull))
