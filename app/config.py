
APP_NAME = 'strappo-api'
TAG = '0.0.1'

DEBUG = False
DEBUG_SQL = False

DEV = False

LOGGER_NAME = APP_NAME
LOG_ENABLE = True
LOG_FORMAT = '[%(process)d] %(levelname)s %(message)s [in %(pathname)s:%(lineno)d]'

DISABLE_HTTP_ACCEPT_CHECK = False
ANALYTICS_IP = '127.0.0.1'

DATABASE_URL = 'sqlite:///appdb.sqlite'

TITANIUM_KEY = 'XXX'
TITANIUM_LOGIN = 'XXX'
TITANIUM_PASSWORD = 'XXX'
TITANIUM_NOTIFICATION_CHANNEL = 'XXX'

EXPIRE_PASSENGERS_AFTER_MINUTES = 100000


try:
    from local_config import *
except ImportError:
    pass
