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


class HiddenDriversGetter(Publisher):
    def perform(self, repository):
        """Search for all the _hidden_ drivers.

        The method will emit a 'hidden_drivers_found' message, followed by the
        list of found drivers.
        """
        self.publish('hidden_drivers_found', repository.get_all_hidden())


class MultipleDriversWithIdGetter(Publisher):
    def perform(self, repository, driver_ids):
        self.publish('drivers_found',
                     filter(None, [repository.get(id) for id in driver_ids]))


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

class ActiveDriverWithIdGetter(Publisher):
    def perform(self, repository, driver_id):
        driver = repository.get_active_by_id(driver_id)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_found', driver)

class DeepDriverWithIdGetter(Publisher):
    def perform(self, repository, driver_id):
        driver = repository.get_with_requests(driver_id)
        if driver is None:
            self.publish('driver_not_found', driver_id)
        else:
            self.publish('driver_found', driver)

class DriverCreator(Publisher):
    def perform(self, repository, user_id, car_make, car_model, car_color,
                license_plate, telephone):
        """Creates a new driver with the specified set of properties.

        On success a 'driver_created' message will be published toghether
        with the created user.
        """
        driver = repository.add(user_id, car_make, car_model, car_color,
                                license_plate, telephone)
        self.publish('driver_created', driver)


class DriverHider(Publisher):
    def perform(self, driver):
        """Temporarily hides the given driver.

        On success, a 'driver_hid' message is published with the updated driver
        record.
        """
        driver.hidden = True
        self.publish('driver_hid', driver)


class MultipleDriversUnhider(Publisher):
    def perform(self, drivers):
        """Sets the 'hidden' property of the given list of drivers to ``False``.

        On success, the 'drivers_unhid' message will be published toghether with
        with the list of unhidden drivers.
        """
        def unhide(driver):
            driver.hidden = False
            return driver
        self.publish('drivers_unhid', [unhide(d) for d in drivers])


def serialize(driver):
    if driver is None:
        return None
    return dict(id=driver.id,
                car_make=driver.car_make,
                car_model=driver.car_model,
                car_color=driver.car_color,
                license_plate=driver.license_plate,
                telephone=driver.telephone,
                hidden=driver.hidden)


class MultipleDriversDeactivator(Publisher):
    def perform(self, drivers):
        def deactivate(d):
            d.active = False
            return d
        self.publish('drivers_hid', [deactivate(d) for d in drivers])


class DriverWithUserIdAuthorizer(Publisher):
    def perform(self, user_id, driver):
        """Checkes if the 'user_id' property of the given driver record matches
        the given user ID.

        An 'authorized' message is published if the given user ID is equal to
        the one associated with the given driver;  otherwise, an 'unauthorized'
        message is sent back to subscribers.
        """
        entitled = user_id == driver.user_id
        if entitled:
            self.publish('authorized', user_id, driver)
        else:
            self.publish('unauthorized', user_id, driver)


class DriverLinkedToPassengerWithUserIdAuthorizer(Publisher):
    def perform(self, user_id, driver):
        """Checks if the 'user_id' property of at least one of the passengers
        contained in the linked drive_requests, matches the given user ID.

        An 'authorized' message is published if the given user is authorized
        to view driver details, otherwise an 'unauthorized' message will be
        sent back to subscribers.
        """
        matching_requests = (user_id == r.passenger.user_id
                             for r in driver.drive_requests)
        if any(matching_requests):
            self.publish('authorized', user_id, driver)
        else:
            self.publish('unauthorized', user_id, driver)


class DriverWithoutDriveRequestForPassengerValidator(Publisher):
    def perform(self, driver, passenger_id):
        matching_requests = (passenger_id == r.passenger.id
                             for r in driver.drive_requests)
        if any(matching_requests):
            self.publish('invalid_driver',
                         dict(_global='Driver request already present'))
        else:
            self.publish('valid_driver', driver)


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


class DriversACSUserIdExtractor(Publisher):
    def perform(self, drivers):
        """Extract ACS user IDs associated with the input list of drivers.

        At the end of the operation a 'acs_user_ids_extracted' message will be
        published, together with the list of the extracted ACS user ids.
        """
        self.publish('acs_user_ids_extracted',
                     filter(None, [d.user.acs_id for d in drivers]))


def enrich(driver):
    return driver

def _enrich(rates_repository, driver):
    from app.pubsub.users import enrich as enrich_user
    driver.user = enrich_user(rates_repository, driver.user)
    return enrich(driver)
