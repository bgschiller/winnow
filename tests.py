from core import Winnow
import nose
from nose.tools import assert_equals

sources = [
    dict(display_name='Number Scoops', column='num_scoops',
         value_types=['numeric', 'nullable']),
    dict(display_name='Flavor', column='flavor',
         value_types=['string'])
]

ice_cream_winnow = Winnow('ice_cream', sources)

def squish_ws(s):
    return ' '.join(s.split()).strip()

def test_basic():
    ice_cream_filt = dict(
        logical_op='|',
        filter_clauses=[
            dict(data_source='Flavor', operator='is', value='Chocolate'),
            dict(
                logical_op='&',
                filter_clauses=[
                    dict(data_source='Number Scoops', operator='>=', value='2'),
                    dict(data_source='Flavor', operator='is', value='Strawberry')
            ])
    ])
    query, params = ice_cream_winnow.query(ice_cream_filt)
    expected = '''
    SELECT * FROM ice_cream
    WHERE
       ((flavor = %s ) OR
        ((num_scoops >= %s) AND (flavor = %s )))'''

    assert_equals(squish_ws(query), squish_ws(expected))
    assert_equals(params, ('Chocolate', 2, 'Strawberry'))

if __name__ == '__main__':
    nose.run()
