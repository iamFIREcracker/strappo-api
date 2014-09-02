#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

from fabric.api import hide
from fabric.api import cd
from fabric.api import env
from fabric.api import local
from fabric.api import put
from fabric.api import run
from fabric.api import require
from fabric.api import settings
from fabric.api import sudo
from fabric.colors import cyan
from fabric.colors import green
from fabric.colors import red
from fabric.decorators import task

from fabfilecommon import *


env.appname = 'strappo-api'
env.appport = '8000'
env.repo_url = 'ssh://hg@bitbucket.org/iamFIREcracker/strappo-api'

@task
def dev():
    env.env_name = 'strappo-ny'

    env.user = 'app'
    env.hosts = ['192.241.139.130']

    env.site_path = '/srv/www/%s' % env.appname
    env.venv_path = '/srv/www/%s/venv' % env.appname
    env.repo_branch = 'develop'

    env.config = 'dev_config.py'

    env.servername = 'api.dev.getstrappo.com'
    env.site_url = 'http://%s/1/info' % env.hosts[0]

@task
def prod():
    env.env_name = 'strappo-am'

    env.user = 'app'
    env.hosts = ['188.226.177.93']

    env.site_path = '/srv/www/%s' % env.appname
    env.venv_path = '/srv/www/%s/venv' % env.appname
    env.repo_branch = 'production'

    env.config = 'prod_config.py'

    env.servername = 'api.getstrappo.com'
    env.site_url = 'http://%s/1/info' % env.hosts[0]


@task
def bootstrap():
    ''' Configure the app '''
    print(cyan("Prerequisites..."))
    prerequisites()

    print(cyan("Cloning repo..."))
    rclone()

    print(cyan("Updating config..."))
    cupload()

    print(cyan("Applying puppet manifest..."))
    papply()

    print(cyan('Creating venv...'))
    vcreate()

    print(cyan('Initialize database...'))
    dbupdate()

    print(cyan('Recreate i18n strings...'))
    i18nupdate()

    restart()

@task
def update():
    ''' Update everything related to the app. '''
    print(cyan("Updating repo..."))
    rupdate()

    print(cyan("Updating config..."))
    cupload()

    print(cyan("Applying puppet manifest..."))
    papply()

    print(cyan('Updating venv...'))
    vupdate()

    print(cyan('Updating database...'))
    dbupdate()

    print(cyan('Recreate i18n strings...'))
    i18nupdate()

    restart()


@task
def restart():
    ''' Restart the app.  Usable from other commands or from the CLI.'''
    print(cyan("Restarting nginx..."))
    sdo("service nginx restart")

    print(cyan("Restarting supervisor..."))
    # XXX Issuing a 'service supervisor restart' will produce an error!!!
    sdo("service supervisor stop && sleep 5 && service supervisor start")
