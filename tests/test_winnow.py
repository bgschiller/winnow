from nose.tools import assert_equals

from .utils import squish_ws
from core import Winnow

sources = [
    dict(display_name='Number Scoops', column='num_scoops',
         value_types=['numeric', 'nullable']),
    dict(display_name='Flavor', column='flavor',
         value_types=['collection']),
]

ice_cream_winnow = Winnow('ice_cream', sources)


def test_basic():
    ice_cream_filt = dict(
        logical_op='&',
        filter_clauses=[
            dict(data_source='Number Scoops', operator='>=', value='2'),
            dict(data_source='Flavor', operator='any of', value=[
                'Strawberry',
                'Chocolate',
            ])
    ])
    query, params = ice_cream_winnow.query(ice_cream_filt)
    expected = '''
    SELECT * FROM ice_cream
    WHERE ((num_scoops >= %s) AND (flavor IN (%s,%s) ))'''

    assert_equals(squish_ws(query), squish_ws(expected))
    assert_equals(params, (2, 'Strawberry', 'Chocolate'))

def test_filters_can_by_nested():
    pass


def test_special_case():
    pass


def test_special_case_override():
    pass
