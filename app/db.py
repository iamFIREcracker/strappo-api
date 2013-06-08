#!/usr/bin/env python
# -*- coding: utf-8 -*-

def populate_db():
    import app.models
    from app.models import Account
    from app.models import ActiveDriver
    from app.models import Driver
    from app.models import Token
    from app.models import User

    app.models.Base.session.add(User(id='uid', name='Name', avatar='Avatar'))
    app.models.Base.session.add(Account(id='aid', user_id='uid',
                                        external_id='eid', type='facebook'))
    app.models.Base.session.add(Token(id='tid', user_id='uid'))
    app.models.Base.session.add(Driver(id='did', user_id='uid',
                                       license_plate='plate',
                                       telephone='1241241'))
    app.models.Base.session.add(ActiveDriver(id='adid', driver_id='did'))
    app.models.Base.session.commit()
