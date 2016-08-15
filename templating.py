from __future__ import unicode_literals
import collections
import datetime
import json
import warnings
import decimal
import jinja2
import random
import string

env = jinja2.Environment(trim_blocks=True)

def render_template(temp_data, *actx, **ctx):
    """
    render a jinja2 template in the custom environment.
    """
    return (env
            .from_string(temp_data)
            .render(*actx, **ctx))

RAND_STRING_ELTS = string.letters
def random_string(length=6):
    """
    Generate a random string for use in pg_quoting.

    With the default length of 6, for an attacker with no extra information to guess
    this value is 1 in 19,770,609,664 or
        - 112 times less likely than winning the Mega Millions (1 in 176 M)
        - 1,977 times less likely than becoming president (1 in 10 M)
        - 3,295 times less likely than dying from bee, hornet, or wasp stings (1 in 6.1 M)
        - 6,590,203 times less likely than being struck by lightning in your lifetime (1 in 3000)

    relevant xkcd: http://xkcd.com/795/

    :param length: the number of random digits
    :return: A random sequence of <length> digits, drawn from RAND_STRING_ELTS
    """
    return ''.join(random.SystemRandom()
            .choice(RAND_STRING_ELTS)
            for _ in range(length))

def register_filter(func):
    env.filters[func.__name__] = func
    return func

@register_filter
def pg_quote(val):
    """
    Create a safely quoted string literal for consumption by postgres.

    Postgres allows you to quote strings like 'hello' using like so:
        $randomletters$hello$randomletters$
    This means that it is difficult/impossible to sustain a SQL-injection attack
    when using one of these dollar-quoted strings, since postgres will just keep
    scanning until it sees the pattern '$randomletters$', where randomletters is
    spontaneously determined at runtime.
    """
    return u'${pattern}${val}${pattern}$'.format(pattern=random_string(), val='{}'.format(val).replace('%', '%%'))

@register_filter
def pg_bool(val):
    return u'true' if val else u'false'

@register_filter
def pg_literal(val):
    """
    Translate a python variable to a valid SQL literal.

    This is a safe method to call (no sql-injection). However, it might not have your
    favorite data-type.
    """
    from utilities import PGJson

    if isinstance(val, (type(None), jinja2.Undefined)):
        return 'NULL'
    if isinstance(val, bool):
        return pg_bool(val)
    if isinstance(val, (int, decimal.Decimal)):
        return str(int(val))
    if isinstance(val, float):
        return '{:.10f}'.format(val)  # 10 oughta be enough, right?
    if isinstance(val, datetime.datetime):
        return "'{}'::timestamp".format(val.isoformat())
    if isinstance(val, basestring):
        return pg_quote(val)
    if isinstance(val, PGJson):
        return "{}::jsonb".format(pg_quote(jsonify(val.adapted)))
    if isinstance(val, (list, dict)):
        return "{}::jsonb".format(pg_quote(jsonify(val)))

    warnings.warn(
        "Didn't recognize value {} of type {}. Attempting to represent as a string.".format(val, type(val)),
        RuntimeWarning)
    return pg_quote(val)


@register_filter
def comma_sep_and_quote(str_list):
    """
    safely quote and comma sep string literals for use in a postgres query.

    If str_list is empty, return a random (unlikely to be found in the db) pattern,
    as querying "id IN ()" is a syntax error. We would rather do "id IN ('adsflkjadsfjl')
    and have it still match nothing.
    """
    if not len(str_list):
        return u"'{}'".format(random_string())  # pattern is alphanumeric, so safe.
    return u', '.join(pg_quote(val) for val in str_list)

@register_filter
def UNSAFE_comma_sep_and_quote(str_list):
    """
    UNSAFELY quote and comma sep string literals for use in a postgres query.

    This just uses regular old ' quotes. It's faster and easier on the eyes, but
    best to use only when you know the input is trusted (eg, a set of opp_ids that
    already came from the db).

    If str_list is empty, return a random (unlikely to be found in the db) pattern,
    as querying "id IN ()" is a syntax error. We would rather do "id IN ('adsflkjadsfjl')
    and have it still match nothing.
    """
    if not len(str_list):
        return u"'{}'".format(random_string())  # pattern is alphanumeric, so safe.
    return u', '.join(u"'{}'".format(val) for val in str_list)

@register_filter
def dt_to_ts(dt):
    """
    Convert a dt to a string representation of a timestamp.
    """
    return u"'{}'::timestamp".format(dt.isoformat())

@register_filter
def row_sep_and_quote(str_list):
    """
    Like comma_sep_and_quote, but for use in a id = ANY(VALUES )call

    This can be as much as 10x faster than id IN ()
    (some sources say 100x faster, but I haven't seen it)
    """
    if not len(str_list):
        return u"(NULL)"
    return u', '.join(u"({})".format(pg_quote(val)) for val in str_list)

@register_filter
def UNSAFE_row_sep_and_quote(str_list):
    """
    Like comma_sep_and_quote, but for use in a id = ANY(VALUES )call
    This can be as much as 10x faster than id IN ()
    (some sources say 100x faster, but I haven't seen it)
    """
    if not len(str_list):
        return u"(NULL)"
    return u', '.join(u"('{}')".format(val) for val in str_list)

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

@register_filter
def jsonify(obj):
    return json.dumps(obj, default=json_custom_parser)

@register_filter
def pg_array(lst):
    return 'array[' + ', '.join(map(pg_quote,lst)) + ']'
