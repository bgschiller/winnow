from __future__ import unicode_literals

import datetime
import decimal
import json
from collections import Iterable

import jinja2
import jinjasql
from jinja2.utils import Markup
from jinjasql.core import _bind_param
from jinjasql.core import _thread_local
from six import string_types


# Replace the bind function to support more types.
def _better_bind(value, name):
    """A filter that prints %s, and stores the value
    in an array, so that it can be bound using a prepared statement
    This filter is automatically applied to every {{variable}}
    during the lexing stage, so developers can't forget to bind
    """
    suffix = ''
    if isinstance(value, Markup):
        return value
    elif isinstance(value, SqlFragment):
        # Copy in the params from the child fragment in order
        for ix, param in enumerate(value.params):
            _thread_local.bind_params['{}#param#{}'.format(name, ix)] = param
        # return the sql unchanged
        return Markup(value.query)
    elif isinstance(value, pg_null):
        suffix = '::' + value.pg_type
        value = None
    if isinstance(value, (dict, PGJson)):
        suffix = '::jsonb'
        value = jsonify(getattr(value, 'adapted', value))
    elif isinstance(value, datetime.datetime):
        suffix = '::timestamp'
    elif isinstance(value, decimal.Decimal):
        value = float(value)
    elif isinstance(value, jinja2.Undefined):
        value = None
    return _bind_param(_thread_local.bind_params, name, value) + suffix


def _anyclause(str_list):
    """
    Like comma_sep_and_quote, but for use in a id = ANY(VALUES )call

    This can be as much as 10x faster than id IN ()
    (some sources say 100x faster, but I haven't seen it)
    """
    values = list(str_list)
    if not len(values):
        return "(NULL)"

    results = []
    for v in values:
        results.append(
            '(' + _bind_param(_thread_local.bind_params, "anyclause", v) + ')')

    clause = ", ".join(results)
    return clause


def _pg_array(lst):
    return 'array[' + ', '.join(
        _bind_param(_thread_local.bind_params, 'pg_array', v)
        for v in lst) + ']'


class WinnowSql(jinjasql.JinjaSql):
    def __init__(self, *args, **kwargs):
        super(WinnowSql, self).__init__(*args, **kwargs)
        self.env.filters['bind'] = _better_bind
        self.env.filters['anyclause'] = _anyclause
        self.env.filters['pg_array'] = _pg_array

    def prepare_query(self, temp_data, **ctx):
        query, params = super(WinnowSql, self).prepare_query(temp_data, ctx)
        return SqlFragment(query, list(params))


def json_custom_parser(obj):
    """
    A custom json parser to handle json.dumps calls properly for Decimal and
    Datetime data types.
    """
    if not isinstance(obj, string_types) and isinstance(obj, Iterable):
        return list(obj)
    elif isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        dot_ix = 19  # 'YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM'.find('.')
        return obj.isoformat()[:dot_ix]
    else:
        raise TypeError(obj)


def jsonify(obj):
    return json.dumps(obj, default=json_custom_parser, sort_keys=True)


class PGJson(object):
    def __init__(self, adapted):
        self.adapted = adapted


class pg_null(object):
    def __init__(self, pg_type):
        self.pg_type = pg_type

    def __unicode__(self):
        return 'NULL::{}'.format(self.pg_type)

    __str__ = __unicode__


class SqlFragment(object):
    """
    A wrapper around (query, params) that supports addition
    """
    def __init__(self, query, params):
        self.query = query
        self.params = params

    def __add__(self, other):
        return SqlFragment(
            query=self.query + other.query,
            params=self.params + other.params)

    def __iter__(self):
        """
        to support
            `cursor.execute(*fragment)`
            `query, params = fragment`
        """
        return iter((self.query, self.params))

    def __eq__(self, other):
        return self.query == other.query and self.params == other.params


    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            repr(self.query),
            repr(self.params))

    __str__ = __unicode__ = __repr__

    @staticmethod
    def join(sep, elems):
        return SqlFragment(
            sep.join(e.query for e in elems),
            tuple(v for e in elems for v in e.params))
