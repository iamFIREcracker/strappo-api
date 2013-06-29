#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher


class UnhiddenDriversGetter(Publisher):
    def perform(self, repository):
        """Search for all the _unhidden_ drivers.

        The method will emit a 'unhidden_drivers_found' message, followed by the
        list of found drivers.
        """
        self.publish('unhidden_drivers_found', repository.get_all_unhidden())


class DriverWithUserIdGetter(Publisher):
    def perform(self, repository, user_id):
        """Search for a driver registered for the specified user ID.

        If such driver exists, a 'driver_found' message is published containing
        driver information;  on the other hand, if no driver exists with the
        specified ID, a 'driver_not_found' message will be published.
        """
        driver = repository.with_user_id(user_id)
        if driver is None:
            self.publish('driver_not_found', user_id)
        else:
            self.publish('driver_found', driver)


class DriverWithIdGetter(Publisher):
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


class DriverCreator(Publisher):
    def perform(self, repository, user_id, license_plate, telephone):
        """Creates a new driver with the specified set of properties.

        On success a 'driver_created' message will be published toghether
        with the created user.
        """
        driver = repository.add(user_id, license_plate, telephone)
        self.publish('driver_created', driver)


class DriverUpdater(Publisher):
    def perform(self, repository, driver_id, license_plate, telephone):
        """Sets the properties 'license_plate' and 'telephone' of the driver
        identified by ``driver_id``.

        If no driver exists identified by ``driver_id``, then a
        'driver_not_found' message is published together with the given driver
        ID;  on the other hand, a 'driver_published' message is published with
        the retrieved record.
        """
        driver = repository.update(driver_id, license_plate, telephone)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_updated', driver)


class DriverDeactivator(Publisher):
    def perform(self, repository, driver_id):
        """Temporarily hides the driver identified by ``driver_id``.

        If no driver exists identified by ``driver_id``, then a
        'driver_not_found' message is published together with the given driver
        ID;  on the other hand, a 'driver_hid' message is published with
        the updated driver record.
        """
        driver = repository.hide(driver_id)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_hid', driver)


class DriverActivator(Publisher):
    def perform(self, repository, driver_id):
        """Unhides the driver identified by ``driver_id``.

        If no driver exists identified by ``driver_id``, then a
        'driver_not_found' message is published together with the given driver
        ID;  on the other hand, a 'driver_hid' message is published with
        the updated driver record.
        """
        driver = repository.unhide(driver_id)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_unhid', driver)


def serialize(driver):
    if driver is None:
        return None
    return dict(id=driver.id, license_plate=driver.license_plate,
            telephone=driver.telephone, hidden=driver.hidden)


class DriverSerializer(Publisher):
    def perform(self, driver):
        """Convert the given driver into a serializable dictionary.

        At the end of the operation the method will emit a 'driver_serialized'
        message containing the serialized object (i.e. driver dictionary).
        """
        from app.pubsub.users import serialize as serialize_user
        d = serialize(driver)
        d.update(user=serialize_user(driver.user))
        self.publish('driver_serialized', d)


class DriversDeviceTokenExtractor(Publisher):
    def perform(self, drivers):
        """Extract the device tokens associated with the input list of drivers.

        At the end of the operation a 'device_tokens_extracted' message will be
        published, together with the list of the extracted device tokens.
        """
        self.publish('device_tokens_extracted',
                     [d.user.device.device_token for d in drivers])
