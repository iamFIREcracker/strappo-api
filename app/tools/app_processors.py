#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from web.contrib.template import render_jinja
from webassets.ext.jinja2 import AssetsExtension

import app.config as config
from app import get_version
from app.assets import env



def load_logger(factory):
    """Add a logger to the shared context.

    Inputs:
        factory logger factory
    """
    def inner():
        web.ctx.logger = factory()
    return inner


def load_path_url():
    """Add path_url property to the shared context."""
    web.ctx.path_url = web.ctx.home + web.ctx.path


def load_render(views):
    """Add the renderer to the shared context.

    Inputs:
        views path containing application views
    """
    render = render_jinja(
            views, encoding='utf-8',
            extensions=['jinja2.ext.do', AssetsExtension])
    render._lookup.assets_environment = env
    render._lookup.globals.update(dict(DEV=config.DEV,
                                        VERSION=get_version()))
    def inner():
        web.ctx.render = render;
    return inner


def load_session(session):
    """Load the session into the shared context.
    
    Inputs:
        session object keeping track of sessions
    """
    def inner():
        web.ctx.session = session
    return inner


def load_sqla(factory):
    """Load SQLAlchemy database session and manage exceptions properly.

    Inputs:
        dbsession database session
    """
    def inner(handler):
        web.ctx.orm = factory()

        try:
            return handler()
        finally:
            factory.remove()
    return inner
