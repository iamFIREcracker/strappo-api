#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue


class Future(object):
    """Extremely simplified implementation of a future (just a wrapper of
    a standard blocking queue).
    """
    def __init__(self):
        self._data = None
        self._data_pushed = self._data_popped = False
        self._queue = Queue.Queue()

    def set(self, value):
        """Sets the object returned by the future.

        This implementation is subject to races, but given that we are going to
        use it in a single-threaded environment we can simply stick with that.
        """
        if not self._data_pushed:
            self._queue.put(value)
            self._data_pushed = True

    def get(self):
        """Gets the object contained by the future.

        This implementation is subject to races, but given that we are going to
        use it in a single-threaded environment we can simply stick with that.
        """
        if not self._data_popped:
            self._data = self._queue.get()
            self._data_popped = True
        return self._data


class Publisher(object):
    """Defines a simple message publisher.

    A publisher is an object with two methods:  the first is needed to register
    'listeners' to the publisher, so that they can be notified when a new
    message is required to be published;  the second is the 'publish' method.

    >>> class WorldHelloer:
    ...   def hello(self):
    ...     print 'Hello, world!'
    >>> class NameHelloer:
    ...   def __init__(self, name):
    ...     self.name = name
    ...   def hello(self):
    ...     print 'Hello, %(name)s!' % dict(name=self.name)

    >>> p = Publisher()
    >>> p.publish('hello')

    >>> p = Publisher()
    >>> p.add_subscriber(WorldHelloer())
    >>> p.publish('hello')
    Hello, world!

    >>> p = Publisher()
    >>> p.add_subscriber(NameHelloer('Foo'), NameHelloer('Bar'))
    >>> p.publish('hello')
    Hello, Foo!
    Hello, Bar!
    """

    def __init__(self):
        """Constructor.

        Initialize the list of subscribers."""
        self.subscribers = []

    def add_subscriber(self, subscriber, *moresubscribers):
        """Adds a new subscriber to the list of publisher subscribers."""
        self.subscribers += [subscriber] + list(moresubscribers)

    def publish(self, message, *args, **kwargs):
        """Publishes ``message`` to all the registered subscribers having
        a method with the name equal to the message.

        For example, if ``message`` is 'hello_world', only those subscribers
        with a method named 'hello_wordld' will be notified of this message."""
        for subscriber in self.subscribers:
            if hasattr(subscriber, message):
                getattr(subscriber, message)(*args, **kwargs)


class LoggingSubscriber(object):
    """A generic subscriber in charge of logging each received event.

    >>> from collections import namedtuple
    >>> Logger = namedtuple('Logger', 'info'.split())
    >>> def info(message):
    ...   print message
    >>> logger = Logger(info)
    >>> this = LoggingSubscriber(logger)

    >>> this.on_button_clicked('Button1')
    Received event='on_button_clicked' args=('Button1',)

    >>> this.on_validation_error('Invalid format')
    Received event='on_validation_error' args=('Invalid format',)
    """
    def __init__(self, logger):
        self.logger = logger

    def __getattr__(self, name):
        def callable(*args):
            msg = 'Received event=%(event)r args=%(args)r'
            msg = msg % dict(event=name, args=args)
            self.logger.info(msg)
        return callable


class FormValidator(Publisher):
    def perform(self, form, params, invalidformdescriber):
        """Validates ``form`` and publish result messages accordingly.

        On success a 'valid_form' message is published with the form just
        validated.  On the other hand, if something went wrong during the
        validaiton, an 'invalid_form' message is published, together with the
        reason of the invalidation.
        """
        if form.validates(**params):
            self.publish('valid_form', form)
        else:
            self.publish('invalid_form', invalidformdescriber(form))


class TaskSubmitter(Publisher):
    def perform(self, task, *args, **kwargs):
        """Spawns the given task asynchronously and publish a 'task_created'
        message containing the ID of the just created task."""
        task_id = task.delay(*args, **kwargs)
        self.publish('task_created', task_id)


class FacebookProfileGetter(Publisher):
    def perform(self, adapter, access_token):
        """Gets the profile information of the user identified by the specified
        access token.

        If something goes wrong while trying to access the profile info, a
        'profile_not_found' message will be published with the error cause;
        on the other hand, a 'profile_found' message containing the profile
        information will be sent back to subscribers."""
        (data, error) = adapter.profile(access_token)
        if error is not None:
            self.publish('profile_not_found', error)
        else:
            data['name'] = adapter.name(data['first_name'], data['last_name'])
            data['avatar'] = adapter.avatar(data['id'])
            self.publish('profile_found', data)
