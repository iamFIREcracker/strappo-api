#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import web


def jsonify(*args, **kwargs):
    """Dumps input arguments into a JSON object.
    
    Note that the 'Content-Type' header is automatically set to JSON.
    """
    web.header('Content-Type', 'application/json')

    return json.dumps(dict(*args, **kwargs))
