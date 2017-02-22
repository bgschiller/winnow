'''winnow/operators.py

This package provides a mapping from stringly-stored
operators to a function implementing that operation.

Only the defaults are implemented here. Clients using winnow
can define additional operators.
'''
from __future__ import unicode_literals

OPERATORS = [
    dict(name='>=', value_type='numeric', negative=False),
    dict(name='<=', value_type='numeric', negative=False),
    dict(name='>', value_type='numeric', negative=False),
    dict(name='<', value_type='numeric', negative=False),
    dict(name='is', value_type='numeric', negative=False),
    dict(name='is not', value_type='numeric', negative=True),
    dict(name='is', value_type='string', negative=False),
    dict(name='is not', value_type='string', negative=True),
    dict(name='contains', value_type='string', negative=False),
    dict(name='starts with', value_type='string', negative=False),
    dict(name='more than __ words', value_type='string_length', coalesced_value_type='numeric', negative=False),
    dict(name='fewer than __ words', value_type='string_length', coalesced_value_type='numeric', negative=False),
    dict(name='any of', value_type='collection', negative=False),
    dict(name='is', value_type='bool', negative=False),
    dict(name='not any of', value_type='collection', negative=True),
    dict(name='within', value_type='relative_date', negative=False),
    dict(name='outside of', value_type='relative_date', negative=True),
    dict(name='after', value_type='absolute_date', negative=False),
    dict(name='before', value_type='absolute_date', negative=False),
    dict(name='is set', value_type='nullable', coalesced_value_type='bool', negative=True),
]


def get_sql_binary_op(op_name):
    if op_name in ('>=', '<=', '>', '<'):
        return op_name
    elif op_name == 'before':
        return '<'
    elif op_name == 'after':
        return '>='
    elif op_name == 'is':
        return '='
    elif op_name == 'is not':
        return '<>'
    else:
        raise NotImplementedError("No SQL binary operator for operator '{}'".format(op_name))
