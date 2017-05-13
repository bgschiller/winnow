'''winnow/values.py

vivify and normalize each of the different field types:
    - string
    - collection (values are strings, left operand is collection)
    - numeric
    - bool
    - date

To vivify is to turn from a string representation into a
 live object. So for '2014-01-21T16:34:02', we would make a
 datetime object. Vivify functions should also accept their
 return type. So vivify_absolute_date(datetime.datetime.now())
 should just return the datetime object.
To stringify is to serialize. This would be like turning the
 list [1, 2, 3] into the JSON string "[1,2,3]"
'''
from __future__ import unicode_literals

import json
from datetime import datetime

from dateutil.parser import parse as parse_date
from six import string_types

from .error import WinnowError
from .relative_dates import valid_rel_date_values

# TODO : Since we're storing filters denormalized as JSON now, we probably need
# Less of this crazy vivification stuff. For another day, perhaps.
def stringify_string(value):
    return str(value)

def stringify_collection(value):
    return json.dumps(value)

stringify_single_choice = json.dumps
stringify_bool = str

def stringify_numeric(value):
    if isinstance(value, float):
        return '{:.10f}'.format(value)
    return str(value)

stringify_absolute_date = datetime.isoformat

def vivify_string(value):  # request for comment -- tighter check on this?
    return str(value)

def vivify_collection(value):
    try:
        if not isinstance(value, list):
            value = json.loads(value)
        assert isinstance(value, list), "collection values must be lists"
        assert all(isinstance(v, (dict, string_types)) for v in value), "elements of collection must be dicts (or strings, for backwards compat)"
        if value and isinstance(value[0], dict):  # backwards compat check.
            value = [v['id'] for v in value]
        return value
    except (ValueError, AssertionError) as e:
        raise WinnowError(e)

def vivify_single_choice(value):
    try:
        if not isinstance(value, dict):
            value = json.loads(value)
        assert isinstance(value, dict), "single choice values must be a dict"
        assert 'id' in value and 'name' in value, "Choice must have keys for 'name' and 'id'"
        return value
    except (ValueError, AssertionError) as e:
        raise WinnowError(e)

def vivify_numeric(value):
    if value == '':
        return 0
    if isinstance(value, (float, int)):
        return value
    try:
        return int(value)
    except ValueError:
        pass  # int is more restrictive -- let's not get hasty
        # and reject before we see if it's a float.
    try:
        return float(value)
    except ValueError as e:
        raise WinnowError(e)


def vivify_relative_date(value):
    if value.lower().replace(' ', '_') in valid_rel_date_values:
        return value.lower().replace(' ', '_')
    raise WinnowError("Invalid relative date value: '{}'".format(value))
stringify_relative_date = vivify_relative_date

def vivify_absolute_date(value):
    try:
        return parse_date(value)
    except TypeError:
        raise WinnowError("invalid literal for date range: '{}'".format(value))

def vivify_bool(value):
    if isinstance(value, string_types) and value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    else:
        assert isinstance(value, bool), "expected boolean or string. received '{}'".format(value)
        return value
