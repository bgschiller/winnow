from core import Winnow

sources = [
    dict(display_name='Number Scoops', column='num_scoops',
         value_types=['numeric', 'nullable']),
    dict(display_name='Flavor', column='flavor',
         value_types=['string'])
]
filt = dict(
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
w = Winnow('ice_cream', sources)
print w.query(filt)
