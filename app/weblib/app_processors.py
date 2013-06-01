#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from web.contrib.template import render_jinja

from weblib.logging import create_logger



def load_logger(logfactory=None):
    '''Add a logger to the shared context.'''
    reallogfactory = create_logger if logfactory is None else logfactory
    def inner():
        web.ctx.logger = reallogfactory()
    return inner


def load_pathurl():
    '''Add path_url property to the shared context.'''
    web.ctx.path_url = web.ctx.home + web.ctx.path


def load_render(views, **globals):
    '''Add the renderer to the shared context.'''
    render = render_jinja(views, encoding='utf-8',
                          extensions=['jinja2.ext.do'])
    render._lookup.globals.update(globals)
    def inner():
        web.ctx.render = render;
    return inner


def load_render_with_assets(views, env, **globals):
    '''Add the renderer to the shared context.'''
    from webassets.ext.jinja2 import AssetsExtension
    render = render_jinja(views, encoding='utf-8',
                          extensions=['jinja2.ext.do', AssetsExtension])
    render._lookup.assets_environment = env
    render._lookup.globals.update(globals)
    def inner():
        web.ctx.render = render;
    return inner


def load_session(session):
    '''Load the session into the shared context.'''
    def inner():
        web.ctx.session = session
    return inner


def load_orm(ormfactory):
    '''Load the database orm layer into the shared context.'''
    def inner():
        web.ctx.orm = ormfactory()
    return inner

def load_manage_orm(ormfactory):
    '''Load ORM database connection and manage exceptions properly.'''
    def inner(handler):
        web.ctx.orm = ormfactory()

        try:
            return handler()
        finally:
            ormfactory.remove()
    return inner
