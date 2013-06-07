#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.repositories.users import UsersRepository
from app.weblib.controllers import AbstractCookieAuthorizedController
from app.weblib.controllers import AbstractParamAuthorizedController


class CookieAuthorizedController(AbstractCookieAuthorizedController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)


class ParamAuthorizedController(AbstractParamAuthorizedController):
    def get_user(self, token):
        return UsersRepository.authorized_by(token)
