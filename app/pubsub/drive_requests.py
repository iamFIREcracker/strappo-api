#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.weblib.pubsub import Publisher
from app.pubsub import serialize_date


class ActiveDriveRequestsFilterExtractor(Publisher):
    def perform(self, params):
        """Decides which search criteria should be used to filter active drive
        requests.
        """
        if 'passenger_id' in params:
            self.publish('by_passenger_id_filter', params.passenger_id)
        elif 'driver_id' in params:
            self.publish('by_driver_id_filter', params.driver_id)
        else:
            self.publish('bad_request', params)


class UnratedDriveRequestWithIdGetter(Publisher):
    def perform(self, repository, id, driver_id, user_id):
        request = repository.get_unrated_by_id(id, driver_id, user_id)
        if request is None:
            self.publish('drive_request_not_found', id)
        else:
            self.publish('drive_request_found', request)


class ActiveDriveRequestsWithDriverIdGetter(Publisher):
    def perform(self, repository, driver_id):
        """Search for all the active drive requests associated with the given
        driver ID.

        When done, a 'drive_requests_found' message will be published,
        followed by the list of drive requests.
        """
        self.publish('drive_requests_found',
                     repository.get_all_active_by_driver(driver_id))


class ActiveDriveRequestsWithPassengerIdGetter(Publisher):
    def perform(self, repository, passenger_id):
        """Search for all the active drive requests associated with the given
        passenger ID.

        When done, a 'drive_requests_found' message will be published,
        followed by the list of drive requests.
        """
        self.publish('drive_requests_found',
                     repository.get_all_active_by_passenger(passenger_id))


class ActiveDriveRequestsGetter(Publisher):
    def perform(self, repository):
        """Search for all the active drive request.

        When done, a 'drive_requests_found' message will be published, toghether
        with the list of active drive requests records.
        """
        self.publish('drive_requests_found', repository.get_all_active())


class UnratedDriveRequestsWithDriverIdGetter(Publisher):
    def perform(self, repository, driver_id, user_id):
        self.publish('drive_requests_found',
                     repository.get_unrated_by_driver_id(driver_id,
                                                         user_id))


class UnratedDriveRequestsWithPassengerIdGetter(Publisher):
    def perform(self, repository, passenger_id, user_id):
        self.publish('drive_requests_found',
                     repository.get_unrated_by_passenger_id(passenger_id,
                                                            user_id))


class DriveRequestCreator(Publisher):
    def perform(self, repository, driver_id, passenger_id, **kw):
        request = repository.add(driver_id, passenger_id, **kw)
        self.publish('drive_request_created', request)


class DriveRequestAcceptor(Publisher):
    def perform(self, repository, driver_id, passenger_id):
        """Marks the ride request between driver identified by ``driver_id`` and
        the passenger identified by ``passenger_id`` as _accepted_.

        On success a 'drive_request_accepted' message with the accepted ride
        request object will be published;  on the other hand a
        'drive_request_not_found' message will be generated.
        """
        request = repository.accept(driver_id, passenger_id)
        if request is None:
            self.publish('drive_request_not_found', driver_id, passenger_id)
        else:
            self.publish('drive_request_accepted', request)


class DriveRequestCancellorByDriverId(Publisher):
    def perform(self, repository, drive_request_id, driver_id):
        request = repository.cancel_by_driver_id(drive_request_id,
                                                 driver_id)
        if request is None:
            self.publish('drive_request_not_found',
                         drive_request_id, driver_id)
        else:
            self.publish('drive_request_cancelled', request)


class DriveRequestCancellorByPassengerId(Publisher):
    def perform(self, repository, drive_request_id, passenger_id):
        request = repository.cancel_by_passenger_id(drive_request_id,
                                                    passenger_id)
        if request is None:
            self.publish('drive_request_not_found',
                         drive_request_id, passenger_id)
        else:
            self.publish('drive_request_cancelled', request)


def serialize(request):
    if request is None:
        return None
    return dict(id=request.id, accepted=request.accepted,
                response_time=request.response_time,
                created=serialize_date(request.created))


def _serialize(request):
    from app.pubsub.drivers import serialize as serialize_driver
    from app.pubsub.passengers import serialize as serialize_passenger
    from app.pubsub.users import serialize as serialize_user
    d = serialize(request)
    d.update(passenger=serialize_passenger(request.passenger))
    d['passenger'].update(user=serialize_user(request.passenger.user))
    d.update(driver=serialize_driver(request.driver))
    d['driver'].update(user=serialize_user(request.driver.user))
    return d


class MultipleDriveRequestsSerializer(Publisher):
    def perform(self, requests):
        """Convert a list of drive requests into serializable dictionaries.

        At the end of the operation, the method will emit a
        'drive_requests_serialized' message containing serialized objects.
        """
        self.publish('drive_requests_serialized',
                     [_serialize(r) for r in requests])


class MultipleDriveRequestsDeactivator(Publisher):
    def perform(self, requests):
        """Sets the 'active' property of the input list of drive requests
        to ``False`` (i.e. hides them).

        When done, a 'drive_requests_hid' message will be published, toghether
        with the list list of amended drive requests records.
        """
        def deactivate(request):
            request.active = False
            return request

        self.publish('drive_requests_hid', [deactivate(r) for r in requests])


class AcceptedDriveRequestsFilter(Publisher):
    def perform(self, requests):
        """Filter out all the requests with 'accepted' equal to `False`.

        When done, an 'accepted_drive_requests' message will be published,
        toghether with list of accepted requests.
        """
        self.publish('drive_requests_extracted',
                     [r for r in requests if r.accepted])

def enrich(request):
    return request

def _enrich(rates_repository, request):
    from app.pubsub.passengers import enrich as enrich_passenger
    from app.pubsub.drivers import enrich as enrich_driver
    from app.pubsub.users import enrich as enrich_user
    request.passenger.user = enrich_user(rates_repository,
                                         request.passenger.user)
    request.passenger = enrich_passenger(request.passenger)
    request.driver.user = enrich_user(rates_repository,
                                         request.driver.user)
    request.driver = enrich_driver(request.driver)
    return enrich(request)

class DriveRequestsEnricher(Publisher):
    def perform(self, rates_repository, requests):
        self.publish('drive_requests_enriched',
                     [_enrich(rates_repository, r) for r in requests])


def _enrich_driver_request(rates_repository, fixed_rate, multiplier, request):
    from app.pubsub.passengers import enrich_with_reimbursement as enrich_passenger
    from app.pubsub.drivers import enrich as enrich_driver
    from app.pubsub.users import enrich as enrich_user
    request.passenger.user = enrich_user(rates_repository,
                                         request.passenger.user)
    request.passenger = enrich_passenger(fixed_rate, multiplier,
                                         request.passenger)
    request.driver.user = enrich_user(rates_repository, request.driver.user)
    request.driver = enrich_driver(request.driver)
    return enrich(request)


class DriverDriveRequestsEnricher(Publisher):
    def perform(self, rates_repository, fixed_rate, multiplier, requests):
        self.publish('drive_requests_enriched',
                     [_enrich_driver_request(rates_repository,
                                             fixed_rate,
                                             multiplier,
                                             r)
                      for r in requests])
