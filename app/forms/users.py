#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form


__all__ = ['add']


def validurl(v):
    """Verifies that the given string starts with 'http://'"""
    return v.startswith('http://')


add = form.Form(form.Textbox('name', form.notnull, description='Name',
                             placeholder='John Smith'),
                form.Textbox('phone', form.notnull, description='Phone',
                             placeholder='(415) 736-0000'),
                form.Textbox('avatar', validurl, description='Avatar',
                             placeholder='http://...'))
