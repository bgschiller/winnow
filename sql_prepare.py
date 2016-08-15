import default_operators
from error import WinnowError

from templating import render_template

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
    if op['value_type'] == 'nullable':
        return '{column} IS{maybe_not} NULL'.format(
            column=column,
            maybe_not=' NOT' if value else '')
    elif op['value_type'] == 'absolute_date':
        return '''({column} {bin_op} '{value}')'''.format(
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value.isoformat()[:19])
    elif op['value_type'] == 'collection':
        return render_template(
            '''({{column}} {{maybe_not}}IN ( {{ value | comma_sep_and_quote }} ))''',
            column=column,
            value=value,
            maybe_not='NOT ' if op['negative'] else '')
    elif op['value_type'] == 'bool':
        return '''({maybe_not}{column})'''.format(
            column=column,
            maybe_not='' if value else 'NOT ')
    elif op['value_type'] == 'numeric':
        return '''({column} {bin_op} {value})'''.format(
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value)
    elif op['value_type'] == 'string':
        if op['name'] == 'contains':
            return render_template('''({{column}} ILIKE '%%' || {{ value | pg_quote }} || '%%')''',
                column=column, value=value)
        elif op['name'] == 'starts with':
            return render_template(
                '''({{column}} ILIKE {{ value | pg_quote }} || '%%')''',
                column=column,
                value=value)
        clause = render_template('''({{column}} {{bin_op}} {{ value | pg_quote }})''',
            column=column,
            bin_op=default_operators.get_sql_binary_op(op['name']),
            value=value)
        # \begin{hack}
        # This hack exists because when folks type a blank string into the filter box,
        # they expect that to catch any null values as well.
        if (op['name'] == 'is' and value == ''):
            return '({clause} OR {column} IS NULL)'.format(clause=clause, column=column)
            # \end{hack}
        return clause
    elif op['value_type'] == 'string_length':
        if op['name'] == 'more than __ words':
            return render_template('''({{column}} ~ '(\S+\s+){{ '{' + value + '}' }}\S+$')''',
                                     column=column, value=str(value))
        elif op['name'] == 'fewer than __ words':
            if value <= 0:
                return '({column} IS NULL)'.format(column=column)
            return render_template('''({{column}} ~ '^(\S+\s+){0,{{ value - 1 }}}\S*$')''',
                                   column=column, value=value)

    else:
        raise WinnowError("Unknown operator type '{}'".format(op['value_type']))
