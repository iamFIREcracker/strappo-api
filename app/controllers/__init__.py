#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web

from app.repositories.users import UsersRepository
from app.weblib.controllers import AbstractCookieAuthorizableController
from app.weblib.controllers import AbstractParamAuthorizableController
from app.weblib.utils import jsonify


class CookieAuthorizableController(AbstractCookieAuthorizableController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)


class ParamAuthorizableController(AbstractParamAuthorizableController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)


class InfoController(object):
    def GET(self):
        return jsonify({
            'min_version':'0.0.1',
            'served_regions':[
                {
                    'name': 'Viareggio',
                    'center': {
                        'lat': 43.873676,
                        'lon': 10.248534
                    },
                    'radius': 10,
                    'hours': [
                         {
                             'day_of_week': 0,
                             'from': 16,
                             'to': 24
                         }, {
                             'day_of_week': 2,
                             'from': 18,
                             'to': 2
                         }, {
                             'day_of_week': 6,
                             'from': 18,
                             'to': 2
                         }
                    ]
                }
            ]
        })
