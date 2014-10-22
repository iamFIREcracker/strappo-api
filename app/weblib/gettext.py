#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import gettext
import os

import web


ALL_TRANSLATIONS = web.storage()


def get_translation(localedir, domain, lang):
    # Init translation.
    if not lang:
        return gettext.NullTranslations()

    try:
        return gettext.translation(domain, localedir, languages=[lang])
    except IOError:
        next_try = lang.split('_')[0]
        next_try = next_try if next_try != lang else ''
        return get_translation(localedir, domain, next_try)


def load_translation(localedir, domain, lang, string):
    if lang not in ALL_TRANSLATIONS:
        translation = get_translation(localedir, domain, lang)
        ALL_TRANSLATIONS[lang] = translation
    return ALL_TRANSLATIONS[lang]


def create_gettext(localedir=None, domain=None):
    if localedir is None:
        localedir = web.config.get('GETTEXT_LOCALE_DIR', 'i18n')
        localedir = os.path.join(os.getcwd(), localedir)

    if domain is None:
        domain = web.config.get('GETTEXT_DOMAIN', 'strings')

    def custom_gettext(string, lang=''):
        lang = lang.replace('-', '_')  # convert en-US into en_US
        translation = load_translation(localedir, domain, lang, string)
        if translation is None:
            return unicode(string)
        return translation.ugettext(string)
    return custom_gettext
