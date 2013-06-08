#!/usr/bin/env bash

cat > local_config.py <<!
DEBUG = False
DEBUG_SQL = False

DEV = True

LOG_ENABLE = False

DATABASE_URL = 'sqlite:///appdb.sqlite'
!

nosetests --with-doctest app/ test/
