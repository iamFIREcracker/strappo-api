APP_NAME = 'poolit'
TAG = '0.0.1'

DEBUG = False
DEBUG_SQL = False

DEV = False

LOGGER_NAME = APP_NAME
LOG_ENABLE = True
LOG_FORMAT = '[%(process)d] %(levelname)s %(message)s [in %(pathname)s:%(lineno)d]'

DATABASE_URL = 'sqlite:///appdb.sqlite'

DISABLE_HTTP_ACCEPT_CHECK = False

try:
    from local_config import *
except ImportError:
    pass
