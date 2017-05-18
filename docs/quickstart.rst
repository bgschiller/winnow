Quickstart
==========

Installation
------------

Winnow is available from PyPI as winnow-filters. I've been having some trouble downloading it from there though -- I'm new to PyPI and it may be set up wrong. In the meantime, it can be installed with

.. code-block:: bash

    pip install git+git://github.com/bgschiller/winnow.git@master


Define your Sources
-------------------

Your sources will usually be a list of the columns you want to make available for filtering. Each source needs a display name and a list of the `value_types` it supports. See :ref:`valuetypes` for a list of included value types.

.. code-block:: python

    sources = [
        {
            'display_name': 'Order Date',
            'column': 'order_date',
            'value_types': ['absolute_date', 'relative_date'] },
        {
            'display_name': 'Number Scoops',
            'column': 'num_scoops',
            'value_types': ['numeric', 'nullable'] },
        {
            'display_name': 'Flavor',
            'column': 'flavor',
            'value_types': ['collection'],
            'picklist_options': [
                'Mint Chocolate Chip',
                'Cherry Garcia',
                'Chocolate',
                'Cookie Dough',
                'Rocky Road',
                'Rainbow Sherbet',
                'Strawberry',
                'Vanilla',
                'Coffee',
             ]},
    ]

Create a Filter
---------------

Use the sources you defined to build a JSON filter. The value types specified on each source determine which operators are available.

.. code-block:: python

    ice_cream_filt = {
        'logical_op': '&',
        'filter_clauses': [
            {'data_source': 'Number Scoops', 'operator': '>=', 'value': '2'},
            {'data_source': 'Flavor', 'operator': 'any of', 'value': [
                'Strawberry',
                'Chocolate',
             ]}
        ]
    }


Get a SQL Query
---------------

Now initialize a :func:`Winnow` instance using your sources, and the name of the table you're filtering against. Turn your filter into a query.

.. code-block:: python

    ice_cream_winnow = Winnow('ice_cream', sources)
    query, params = ice_cream_filt.query(ice_cream_filt)
    # query => SELECT * FROM ice_cream WHERE ((num_scoops >= %s) AND (flavor IN (%s,%s) ))
    # params => (2, 'Strawberry', 'Chocolate')
