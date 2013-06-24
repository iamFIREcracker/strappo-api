#!/usr/bin/env python
# -*- coding: utf-8 -*-

def populate_db():
    import app.models
    from app.models import Account
    from app.models import Driver
    from app.models import Passenger
    from app.models import RideRequest
    from app.models import Token
    from app.models import User

    # One logged driver
    app.models.Base.session.add(User(id='uid', name='Name',
                                     avatar='http://www.placehold.it/128x128/86EF00/AAAAAA&text=no+image'))
    app.models.Base.session.add(Account(id='aid', user_id='uid',
                                        external_id='eid', type='facebook'))
    app.models.Base.session.add(Token(id='tid', user_id='uid'))
    app.models.Base.session.add(Driver(id='did', user_id='uid',
                                       license_plate='plate',
                                       telephone='1241241'))


    # Two passengers
    app.models.Base.session.add(User(id='uid2', name='Name', 
                                     avatar='http://www.placehold.it/128x128/ED3CE1/AAAAAA&text=no+image'))
    app.models.Base.session.add(Passenger(id='pid2', user_id='uid2',
                                          origin='origin2',
                                          destination='destination2',
                                          buddies=2))
    app.models.Base.session.add(User(id='uid3', name='Name',
                                     avatar='http://www.placehold.it/128x128/3C98ED/AAAAAA&text=no+image'))
    app.models.Base.session.add(Passenger(id='pid3', user_id='uid3',
                                          origin='origin3',
                                          destination='destination3',
                                          buddies=3))

    # One accepted passenger
    app.models.Base.session.add(User(id='uid4', name='Name',
                                     avatar='http://www.placehold.it/128x128/C389DE/AAAAAA&text=no+image'))
    app.models.Base.session.add(Passenger(id='pid4', user_id='uid4',
                                          origin='origin4',
                                          destination='destination4',
                                          buddies=3))
    app.models.Base.session.add(RideRequest(id='rrid1', driver_id='did',
                                            passenger_id='pid4', accepted=True))

    # And one waiting for passenger confirmation
    app.models.Base.session.add(User(id='uid5', name='Name',
                                     avatar='http://www.placehold.it/128x128/C83D9E/AAAAAA&text=no+image'))
    app.models.Base.session.add(Passenger(id='pid5', user_id='uid5',
                                          origin='origin5',
                                          destination='destination5',
                                          buddies=2))
    app.models.Base.session.add(RideRequest(id='rrid2', driver_id='did',
                                            passenger_id='pid5', accepted=False))

    app.models.Base.session.commit()
