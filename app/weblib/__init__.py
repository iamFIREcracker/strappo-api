#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.webapi import _status_code
from web.webapi import Redirect


nocontent = NoContent = _status_code("204 No Content")

class Created(Redirect):
    """A `201 Created` response."""
    def __init__(self, url, absolute=False):
        Redirect.__init__(self, url, '201 Created', absolute=absolute)

created = Created
