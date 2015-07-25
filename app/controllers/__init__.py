#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from strappon.repositories.users import UsersRepository
from weblib.controllers import AbstractCookieAuthorizableController
from weblib.controllers import AbstractParamAuthorizableController
from weblib.utils import jsonify


class CookieAuthorizableController(AbstractCookieAuthorizableController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)


class ParamAuthorizableController(AbstractParamAuthorizableController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)


class InfoController(object):
    def GET(self):
        return jsonify({
            'min_version_android': web.config.APP_MIN_VERSION_ANDROID,
            'min_version_ios': web.config.APP_MIN_VERSION_IOS,
            'min_version': web.config.APP_MIN_VERSION,
            'served_regions': web.config.APP_SERVED_REGIONS
        })
