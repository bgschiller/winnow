from __future__ import unicode_literals
import collections
import datetime
import json
import warnings
import decimal
import jinjasql
import jinja2
import collections

# Monkey Patch the bind function to support more types.
from jinja2.utils import Markup
from jinjasql.core import (
    _bind_param, _thread_local, requires_in_clause, MissingInClauseException,
    InvalidBindParameterException, is_dictionary)

def bind(value, name):
    """A filter that prints %s, and stores the value
    in an array, so that it can be bound using a prepared statement
    This filter is automatically applied to every {{variable}}
    during the lexing stage, so developers can't forget to bind
    """
    suffix = ''
    if isinstance(value, Markup):
        return value
    elif isinstance(value, pg_null):
        return value

    if isinstance(value, (list, dict, PGJson)):
        suffix = '::jsonb'
        value = jsonify(getattr(value, 'adapted', value))
    elif isinstance(value, datetime.datetime):
        suffix = '::timestamp'
    elif isinstance(value, decimal.Decimal):
        value = float(value)
    elif isinstance(value, jinja2.Undefined):
        value = None
    return _bind_param(_thread_local.bind_params, name, value) + suffix

import jinjasql.core
jinjasql.core.bind = bind

j = jinjasql.JinjaSql()

class SqlFragment(object):
    def __init__(self, query, params):
        self.query = query
        self.params = params

    def __add___(self, other):
        return SqlFragment(self.query + other.query, self.params + other.params)

    @staticmethod
    def join(sep, elems):
        return SqlFragment(
            sep.join(e.query for e in elems),
            tuple(v for e in elems for v in e.params))

def render_template(temp_data, **ctx):
    """
    render a jinja2 template in the custom environment.
    """
    query, params = j.prepare_query(temp_data, ctx)
    return SqlFragment(query, params)

class pg_null(object):
    def __init__(self, pg_type):
        self.pg_type = pg_type

    def __unicode__(self):
        return 'NULL::{}'.format(self.pg_type)

    __str__ = __unicode__

def register_filter(func):
    j.env.filters[func.__name__] = func
    return func

@register_filter
def anyclause(str_list):
    """
    Like comma_sep_and_quote, but for use in a id = ANY(VALUES )call

    This can be as much as 10x faster than id IN ()
    (some sources say 100x faster, but I haven't seen it)
    """
    values = list(value)
    if not len(values):
        return u"(NULL)"

    results = []
    for v in values:
        results.append('(' + _bind_param(_thread_local.bind_params, "anyclause", v) + ')')

    clause = ", ".join(results)
    return clause


@register_filter
def pg_array(lst):
    return 'array[' + ', '.join(
        _bind_param(_thread_local.bind_params, 'pg_array', v)
        for v in lst) + ']'


def json_custom_parser(obj):
    """
        A custom json parser to handle json.dumps calls properly for Decimal and Datetime data types.
    """
    if not isinstance(obj, basestring) and isinstance(obj, collections.Iterable):
        return list(obj)
    elif isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        dot_ix = 19 # 'YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM'.find('.')
        return obj.isoformat()[:dot_ix]
    else:
        raise TypeError(obj)

def jsonify(obj):
    return json.dumps(obj, default=json_custom_parser)

class PGJson(object):
    def __init__(self, adapted):
        self.adapted = adapted
