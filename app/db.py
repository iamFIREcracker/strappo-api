#!/usr/bin/env python
# -*- coding: utf-8 -*-

def populate_db():
    import app.models
    from app.models import Account
    from app.models import Device
    from app.models import Driver
    from app.models import Passenger
    from app.models import RideRequest
    from app.models import Token
    from app.models import User

    # One logged driver
    app.models.Base.session.add(User(id='uid', name='Matteo L.',
                                     avatar='http://www.placehold.it/128x128/86EF00/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid', user_id='uid',
                                       device_token='6382c63bcf164e72095a7c063195842e065152c5c8019e844d28e9bd7c22a1c4'))
    app.models.Base.session.add(Account(id='aid', user_id='uid',
                                        external_id='eid', type='facebook'))
    app.models.Base.session.add(Token(id='tid', user_id='uid'))
    app.models.Base.session.add(Driver(id='did', user_id='uid',
                                       license_plate='LU127AE',
                                       telephone='+3281234567'))


    # Two passengers
    app.models.Base.session.add(User(id='uid2', name='Giovanni B.', 
                                     avatar='http://www.placehold.it/128x128/ED3CE1/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid2', user_id='uid2',
                                       device_token='dtid2'))
    app.models.Base.session.add(Passenger(id='pid2', user_id='uid2',
                                          origin='Caffe` Vip',
                                          destination='Mojito Bar',
                                          seats=1))
    app.models.Base.session.add(User(id='uid3', name='Alessio B.',
                                     avatar='http://www.placehold.it/128x128/3C98ED/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid3', user_id='uid3',
                                       device_token='dtid2'))
    app.models.Base.session.add(Passenger(id='pid3', user_id='uid3',
                                          origin='Club Negroni',
                                          destination='Macondo',
                                          seats=2))

    # One accepted passenger
    app.models.Base.session.add(User(id='uid4', name='Gabriele R.',
                                     avatar='http://www.placehold.it/128x128/C389DE/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid4', user_id='uid4',
                                       device_token='dtid2'))
    app.models.Base.session.add(Passenger(id='pid4', user_id='uid4',
                                          origin='Viareggio Scalo',
                                          destination='Cosmopolitan',
                                          seats=2))
    app.models.Base.session.add(RideRequest(id='rrid1', driver_id='did',
                                            passenger_id='pid4', accepted=True))

    # And one waiting for passenger confirmation
    app.models.Base.session.add(User(id='uid5', name='Stefano P.',
                                     avatar='http://www.placehold.it/128x128/C83D9E/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid5', user_id='uid5',
                                       device_token='dtid2'))
    app.models.Base.session.add(Passenger(id='pid5', user_id='uid5',
                                          origin='Via dei Lecci 123',
                                          destination='Cosmopolitan',
                                          seats=2))
    app.models.Base.session.add(RideRequest(id='rrid2', driver_id='did',
                                            passenger_id='pid5', accepted=False))


    # One hidden driver
    app.models.Base.session.add(User(id='uid6', name='Mario R.',
                                     avatar='http://www.placehold.it/128x128/F06E08/AAAAAA&text=no+image'))
    app.models.Base.session.add(Device(id='deid6', user_id='uid6',
                                       device_token='dtid2'))
    app.models.Base.session.add(Account(id='aid6', user_id='uid6',
                                        external_id='eid6', type='facebook'))
    app.models.Base.session.add(Token(id='tid6', user_id='uid6'))
    app.models.Base.session.add(Driver(id='did6', user_id='uid6',
                                       license_plate='MI17D12',
                                       telephone='+3287126534', hidden=True))


    app.models.Base.session.commit()
