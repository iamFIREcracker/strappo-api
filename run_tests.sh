#!/usr/bin/env bash

cat > local_config.py <<!
debug = False
debug_sql = False

DEV = True

LOG_ENABLE = False

DATABASE_URL = 'sqlite:///appdb.sqlite'
!

nosetests --with-doctest app/ test/
