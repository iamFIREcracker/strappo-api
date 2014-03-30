#!/usr/bin/env python
# -*- coding: utf-8 -*-


def describe_invalid_form(form):
    """Describes the reasons why ``form`` has been invalidated.

    The function iterates on all the 'input' fields of the given form in order
    to extract the associated invalidation note.

    A dictionary containing the names of the input fields as keys, and
    validation errors as values is returned:
    {
        'field1': 'Required',
        'field2': 'Invalid (e.g. MM/DD/YYYY)'
    }
    """
    return dict((i.name, i.note) for i in form.inputs if i.note is not None)


def describe_invalid_form_localized(gettext, lang):
    def inner(form):
        return dict((i.name, gettext(i.note, lang=lang))
                    for i in form.inputs if i.note is not None)
    return inner

