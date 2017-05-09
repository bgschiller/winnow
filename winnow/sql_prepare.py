from . import default_operators
from .error import WinnowError
from .templating import WinnowSql

def sql_type(value_type):
    if value_type in ('absolute_date', 'relative_date'):
        return 'timestamp'
    elif value_type in ('bool', 'numeric'):
        return value_type
    return None

def where_clause(column, op, value):
    """
    Convert a default case filter clause into a WHERE clause.

    Expects a column, operator, and a value.
    """
    w = WinnowSql()
    if op['value_type'] == 'nullable':
        return w.prepare_query(
            '{{ column | sqlsafe }} IS {{ maybe_not | sqlsafe }} NULL',
            column=column,
            maybe_not=' NOT' if value else '')
    elif op['value_type'] == 'absolute_date':
        return w.prepare_query(
            '''({{ column | sqlsafe }} {{ bin_op | sqlsafe }} {{ value  }})''',
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value)
    elif op['value_type'] == 'collection':
        return w.prepare_query(
            '''({{column | sqlsafe }} {{ maybe_not | sqlsafe }} IN {{ value | inclause }} )''',
            column=column,
            value=value,
            maybe_not='NOT' if op['negative'] else '')
    elif op['value_type'] == 'bool':
        return w.prepare_query(
            '''({{ maybe_not | sqlsafe }} {{ column |sqlsafe }})''',
            column=column,
            maybe_not='' if value else 'NOT ')
    elif op['value_type'] == 'numeric':
        return w.prepare_query('''({{ column | sqlsafe }} {{ bin_op | sqlsafe }} {{ value  }})''',
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value)
    elif op['value_type'] == 'string':
        if op['name'] == 'contains':
            return w.prepare_query(
            '''({{ column | sqlsafe }} ILIKE '%%' || {{ value }} || '%%')''',
                column=column, value=value)
        elif op['name'] == 'starts with':
            return w.prepare_query(
                '''({{ column | sqlsafe }} ILIKE {{ value }} || '%%')''',
                column=column,
                value=value)
        return w.prepare_query(
            '''({{ column | sqlsafe }} {{ bin_op | sqlsafe }} {{ value }}
            {% if op_name == 'is' and value == '' %}
                {# \begin{hack}
                This hack exists because when folks type a blank string into the filter box,
                they expect that to catch any null values as well.
                #}
                OR {{ column | sqlsafe }} IS NULL
            {% endif %}
            )''',
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value)
    elif op['value_type'] == 'string_length':
        if op['name'] == 'more than __ words':
            regex = '(\S+\s+){' + str(int(value)) + '}\S+$'
            return w.prepare_query(
                '''({{ column | sqlsafe }} ~ {{ regex | sqlsafe }} )''',
                                     column=column, regex=regex)
        elif op['name'] == 'fewer than __ words':
            if value <= 0:
                return '({column} IS NULL)'.format(column=column)
            regex = '^(\S+\s+){0,' + str(int(value) - 1) + '}\S*$'
            return w.prepare_query('''({{column}} ~ {{ regex | sqlsafe }})''',
                                   column=column, regex=regex)
    else:
        raise WinnowError("Unknown operator type '{}'".format(op['value_type']))
