#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web import form


add = form.Form(form.Textbox('license_plate', form.notnull,
                             description='License Plate',
                             placeholder='TR6 1971'),
                form.Textbox('telephone', form.notnull,
                             description='Telephone',
                             placeholder='+1 416-915-8200'))


update = form.Form(form.Textbox('license_plate', form.notnull,
                                description='License Plate',
                                placeholder='TR6 1971'),
                   form.Textbox('telephone', form.notnull,
                                description='Telephone',
                                placeholder='+1 416-915-8200'))

