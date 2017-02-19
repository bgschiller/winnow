from nose.tools import assert_equals

from core import Winnow
from utils import squish_ws

sources = [
    dict(display_name='Number Scoops', column='num_scoops',
         value_types=['numeric', 'nullable']),
    dict(display_name='Flavor', column='flavor',
         value_types=['collection'],
         picklist_options=[
            'Mint Chocolate Chip',
            'Cherry Garcia',
            'Chocolate',
            'Cookie Dough',
            'Rocky Road',
            'Rainbow Sherbet',
            'Strawberry',
            'Vanilla',
            'Coffee',
         ]),
    dict(display_name='More Scoops than Avg', value_types=['bool']),
 ]

@Winnow.special_case('More Scoops than Avg', 'bool')
def more_scoops_than_avg(wnw, clause):
    return wnw.prepare_query(
        squish_ws('''
        num_scoops
        {% if yes_more %} > {% else %} <= {% endif %}
        (SELECT AVG(num_scoops) FROM ice_cream)
        '''),
        yes_more=clause['value_vivified'])


@Winnow.special_case('Number Scoops', 'nullable')
def number_scoops_nullable(wnw, clause):
    return wnw.prepare_query(
        squish_ws('''
        NULLIF(num_scoops, 0)
        {% if is_set %} IS NOT NULL {% else %} IS NULL {% endif %}
        '''),
        is_set=clause['value_vivified'])

ice_cream_winnow = Winnow('ice_cream', sources)

ice_cream_filt = dict(
    logical_op='&',
    filter_clauses=[
        dict(data_source='Number Scoops', operator='>=', value='2'),
        dict(data_source='Flavor', operator='any of', value=[
            'Strawberry',
            'Chocolate',
        ])
])

def test_basic():
    query, params = ice_cream_winnow.query(ice_cream_filt)
    expected = '''
    SELECT * FROM ice_cream
    WHERE ((num_scoops >= %s) AND (flavor IN (%s,%s) ))'''

    assert_equals(squish_ws(query), squish_ws(expected))
    assert_equals(params, (2, 'Strawberry', 'Chocolate'))


nested_filt = dict(
    logical_op='|',
    filter_clauses=[
        ice_cream_filt,
        dict(data_source='Flavor', operator='not any of', value=[
            'Mint Chocolate Chip', 'Cherry Garcia',
        ])
    ]
)

def test_filters_can_by_nested():
    query, params = ice_cream_winnow.where_clauses(nested_filt)
    expected = '''
    (((num_scoops >= %s) AND (flavor IN (%s,%s) ))
     OR (flavor NOT IN (%s,%s) ))'''

    assert_equals(squish_ws(query), squish_ws(expected))
    assert_equals(
        params,
        (2, 'Strawberry', 'Chocolate', 'Mint Chocolate Chip', 'Cherry Garcia'))


special_filt = dict(
    logical_op='&',
    filter_clauses=[
        dict(
            data_source='More Scoops than Avg',
            operator='is',
            value=True)
    ]
)

def test_special_case():
    query, params = ice_cream_winnow.where_clauses(special_filt)
    expected = '(num_scoops  >  (SELECT AVG(num_scoops) FROM ice_cream))'

    assert_equals(query, expected)
    assert_equals(params, ())


overridden_operator_filt = dict(
    logical_op='&',
    filter_clauses=[
        dict(
            data_source='Number Scoops',
            operator='is set',
            value=True)
    ]
)

def test_special_case_override():
    query, params = ice_cream_winnow.where_clauses(overridden_operator_filt)
    expected = '(NULLIF(num_scoops, 0)  IS NOT NULL )'

    assert_equals(query, expected)
    assert_equals(params, ())
