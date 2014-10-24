#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from app.models import Feedback


class FeedbacksRepository(object):
    @staticmethod
    def add(user_id, message):
        feedback = Feedback(id=unicode(uuid.uuid4()), user_id=user_id,
                            message=message)
        return feedback
