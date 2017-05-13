from __future__ import unicode_literals

import copy
import json

from six import string_types

from . import default_operators
from . import sql_prepare
from . import values
from .error import WinnowError
from .templating import SqlFragment
from .templating import WinnowSql

class Winnow(object):
    """
    Winnow is a SQL query builder specifically designed for
     powerful filtering on a table. It is designed to be
     efficient and low-magic.
    """
    # Take care here -- In order to avoid mucking up the parent's copy of this
    # static value we have to deep copy it to every subclass.
    _special_cases = {}

    sql_class = WinnowSql

    def __init__(self, table, sources):
        self.table = table
        self.sources = sources
        self.sql = self.sql_class()

    def prepare_query(self, *args, **kwargs):
        """
        Proxy to self.sql
        """
        return self.sql.prepare_query(*args, **kwargs)

    def resolve(self, filt):
        """
        Given a filter, resolve (expand) all it's clauses.
        A resolved clause includes information about the
        value type of the data source, and how to perform
        queries against that data source.

        return the modified filter.
        """

        filt['logical_op'] = filt.get('logical_op', '&')
        if filt['logical_op'] not in '&|':
            raise WinnowError("Logical op must be one of &, |. Given: {}".format(
                filt['logical_op']))
        for ix in range(len(filt['filter_clauses'])):
            filt['filter_clauses'][ix] = self.resolve_clause(
                filt['filter_clauses'][ix])
        return filt

    def validate(self, filt):
        """
        Make sure a filter is valid (resolves properly), but avoid bulking up
        the json object (probably because it's about to go into the db, or
        across the network)
        """
        self.resolve(copy.deepcopy(filt))
        return filt

    def resolve_clause(self, filter_clause):
        """
        Given a filter_clause, check that it's valid.
        Return a dict-style filter_clause with a vivified
        value field.
        """
        if 'logical_op' in filter_clause:
            # nested filter
            return self.resolve(filter_clause)

        ds, op = self.resolve_components(filter_clause)
        value = self.vivify(op['value_type'], filter_clause['value'])
        filter_clause['data_source_resolved'] = ds
        filter_clause['operator_resolved'] = op
        filter_clause['value_vivified'] = value
        filter_clause['summary'] = self.summarize(filter_clause)
        return filter_clause

    def summarize(self, filter_clause):
        ds = filter_clause['data_source_resolved']
        op = filter_clause['operator_resolved']
        value = filter_clause['value_vivified']

        cvt = self.coalesce_value_type(op['value_type'])
        value_string = value
        operator_string = op.get('summary_template') or '{{data_source}} {} {{value}}'.format(op['name'])
        if cvt == 'collection':
            operator_string, value_string = self.summarize_collection(filter_clause)
        elif cvt == 'relative_date':
            value_string = value.replace('_', ' ')
        elif cvt == 'numeric':
            value_string = '{:,}'.format(value)
        return operator_string.format(data_source=ds['display_name'], value=value_string)

    @classmethod
    def coalesce_value_type(cls, value_type):
        for op in cls.operators:
            if op['value_type'] == value_type:
                return op.get('coalesced_value_type', value_type)
        return value_type

    @classmethod
    def summarize_collection(cls, filter_clause):
        value = filter_clause['value'] if isinstance(filter_clause['value'], list) else json.loads(filter_clause['value'])

        operator_string = '{data_source} any of {value}' if len(value) != 1 else '{data_source} is {value}'
        if not value:
            value_string = '(none)'
        else:
            value_string = ', '.join(value)
        return operator_string, value_string

    @staticmethod
    def empty_filter():
        return dict(logial_op='&', filter_clauses=[])

    @classmethod
    def vivify(cls, value_type, value):
        """De-stringify <value> into <value_type>

        Raises WinnowError if <value> is not well formatted for that type."""
        cvt = cls.coalesce_value_type(value_type)
        if cvt == 'string':
            return values.vivify_string(value)
        elif cvt == 'collection':
            return values.vivify_collection(value)
        elif cvt in ('numeric', 'string_length'):
            return values.vivify_numeric(value)
        elif cvt == 'relative_date':
            return values.vivify_relative_date(value)
        elif cvt == 'absolute_date':
            return values.vivify_absolute_date(value)
        elif cvt in ('bool', 'nullable'):
            return values.vivify_bool(value)
        elif cvt == 'single_choice':
            return values.vivify_single_choice(value)
        else:
            raise WinnowError("Unknown value_type, '{}'".format(value_type))

    @classmethod
    def stringify(cls, value_type, value):
        cvt = cls.coalesce_value_type(value_type)
        if isinstance(value, string_types):
            value = cls.vivify(value_type, value)

        if cvt == 'string':
            return values.stringify_string(value)
        elif cvt == 'collection':
            return values.stringify_collection(value)
        elif cvt in ('numeric', 'string_length'):
            return values.stringify_numeric(value)
        elif cvt == 'relative_date':
            return values.stringify_relative_date(value)
        elif cvt == 'absolute_date':
            return values.stringify_absolute_date(value)
        elif cvt in ('bool', 'nullable'):
            return values.stringify_bool(value)
        elif cvt == 'single_choice':
            return values.stringify_single_choice(value)
        raise WinnowError("Unknown value_type, '{}'".format(value_type))

    operators = default_operators.OPERATORS

    def resolve_operator(self, op_name, value_types):
        '''Given an operator name, return an Op object.

        Raise an error if the operator is not found'''
        if not isinstance(op_name, string_types):
            raise WinnowError("Bad operator type, '{}'. expected string".format(type(op_name)))
        op_name = op_name.lower()
        matches = [op for op in self.operators
                   if op['name'].lower() == op_name and op['value_type'] in value_types]
        if len(matches) == 0:
            raise WinnowError("Unknown operator '{}'".format(op_name))
        return matches.pop()

    def resolve_source(self, source_name):
        """
        Given a source name, return a resolved data source.

        Raise an error if the source name is not allowable
        """

        matches = [source for source in self.sources
                   if source['display_name'] == source_name]
        if len(matches) == 0:
            raise WinnowError("Unknown data source '{}'".format(source_name))
        elif len(matches) > 1:
            raise WinnowError("Ambiguous data source '{}'".format(source_name))
        return matches.pop()

    def resolve_components(self, clause):
        source = self.resolve_source(clause['data_source'])
        operator = self.resolve_operator(clause['operator'],
                                         source['value_types'])
        return source, operator

    def query(self, filt):
        return self.prepare_query(
            "SELECT * FROM {{ table | sqlsafe }} WHERE {{ condition }}",
            table=self.table,
            condition=self.where_clauses(filt))

    def strip(self, filt):
        """
        Perform the opposite of resolving a filter.
        """
        for k in ('data_source_resolved', 'operator_resolved', 'value_vivified'):
            filt.pop(k, None)
        if 'filter_clauses' in filt:
            filt['filter_clauses'] = [self.strip(f) for f in filt['filter_clauses']]
        return filt

    def where_clauses(self, filt):
        '''
        Apply a user filter.

        Returns a paren-wrapped WHERE clause suitable for using
        in a SELECT statement on the opportunity table.
        '''
        if not filt['filter_clauses']:
            return True

        filt = self.resolve(filt)
        where_clauses = []
        for clause in filt['filter_clauses']:
            if 'logical_op' in clause:
                # nested filter
                where_clauses.append(self.where_clauses(clause))
            elif 'data_source_resolved' in clause:
                where_clauses.append(self._dispatch_clause(clause))
            else:
                # I don't expect to ever get here, because we should hit this
                # issue when we call `filt = self.resolve(filt)`
                raise WinnowError("Somehow, this is neither a nested filter, nor a resolved clause")


        if not where_clauses:
            return True

        sep = '\nAND \n  ' if filt['logical_op'] == '&' else '\nOR \n  '
        self.strip(filt)
        sql_frag = SqlFragment.join(sep, where_clauses)
        sql_frag.query = '(' + sql_frag.query + ')'
        return sql_frag

    def _dispatch_clause(self, clause):
        """
        Evaluates whether a clause is standard, special, or custom
        and calls the appropriate specialization function.

        Each specialization returns a paren-wrapped WHERE clause, to be AND'd or OR'd
        together to produce a final clause."""
        for k in ('data_source_resolved', 'operator_resolved', 'value_vivified'):
            if k not in clause:
                raise WinnowError('failed to resolve component: {}'.format(k))

        op = clause['operator_resolved']

        special_handler = self.special_case_handler(
            source_name=clause['data_source'],
            value_type=op['value_type'])
        if special_handler is not None:
            return special_handler(self, clause)

        return self._default_clause(clause)

    def where_clause(self, column, op, value):
        return sql_prepare.where_clause(column, op, value)

    def _default_clause(self, clause):
        """
        Given a filter_clause, convert it to a WHERE clause
        """
        ds = clause['data_source_resolved']
        op = clause['operator_resolved']
        value = clause['value_vivified']
        return self.where_clause(ds['column'], op, value)

    @classmethod
    def special_case(cls, source_name, *value_types):
        """
        Register a special case handler. A special case handler is a function s:
         s(Winnow(), clause) -> WHERE clause string
        """
        if cls._special_cases is getattr(super(cls, cls), '_special_cases', None):
            raise RuntimeError('Please define your own _special_cases dict, so as to avoid modifying your parent. '
                               'Note to self: come up with a more durable way to handle this.')
            # ideas:
            # proxy the _special_cases as the union of own and parent's version.

        def decorator(func):
            """
            Register a function in the handler table.
            """
            for value_type in value_types:
                if (source_name, value_type) in cls._special_cases:
                    raise WinnowError("Conflicting handlers registered for ({},{}): {} and {}".format(
                        value_type, source_name,
                        cls._special_cases[(source_name, value_type)].__name__, func.__name__))
                cls._special_cases[(source_name, value_type)] = func
            return func
        return decorator

    def special_case_handler(self, source_name, value_type):
        """
        Check if a given value_type, source_name pair has
        a special case handler.

        :return: A function handler for that case accepting
         the winnow instance and the clause.
        """
        return self._special_cases.get((source_name, value_type))
