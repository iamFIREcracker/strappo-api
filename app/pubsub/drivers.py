#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class DriverGetter(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def driver_not_found(self, driver_id):
    ...     print 'Driver not found: %(driver_id)s' % locals()
    ...   def driver_found(self, driver):
    ...     print 'Driver found: %(driver)s' % locals()
    >>> this = DriverGetter()
    >>> this.add_subscriber(Subscriber())
    
    >>> repo = Mock(get=MagicMock(return_value=None))
    >>> this.perform(repo, 'not_existing_id')
    Driver not found: not_existing_id

    >>> repo = Mock(get=MagicMock(return_value='driver'))
    >>> this.perform(repo, 'existing_id')
    Driver found: driver
    """

    def perform(self, repository, driver_id):
        """Search for a driver identified by ``driver_id``.

        If such driver exists, a 'driver_found' message is published containing
        driver information;  on the other hand, if no driver exists with the
        specified ID, a 'driver_not_found' message will be published.
        """
        driver = repository.get(driver_id)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_found', driver)


class DriverSerializer(Publisher):
    def perform(self, driver):
        """Convert the given driver into a serializable dictionary.

        At the end of the operation the method will emit a 'driver_serialized'
        message containing the serialized object (i.e. driver dictionary).
        """
        self.publish('driver_serialized',
                     dict(id=driver.id, user_id=driver.user_id,
                          license_plate=driver.license_plate,
                          telephone=driver.telephone, active=None))
