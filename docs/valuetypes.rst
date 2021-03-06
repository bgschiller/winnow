.. _valuetypes:

Value Types and Operators
=========================

A value type corresponds to the shape of the ``value`` key in a filter. It might be numeric (``3``), or string (``Mad-Eye Moody``) or relative_date (``last_7_days``). Each operator specifes the unique value type it operates on. Each data_source can list any number of value types it will support.

For example, "Order Date" source from our quickstart example lists that it supports both relative_date and absolute_date. The values for relative_date look like ``last_month`` or ``next_7_days``. The values for absolute_date look like ``2017-05-18T12:30``. Because both absolute\_ and relative_date value_types are supported for "Order Date", we can use the relative_date operators (``within`` and ``outside of``) as well as the absolute_date operators (``before`` and ``after``).

The existing value types and operators can be easily extended by subclassing Winnow. We will see out to do this in :ref:`extending_winnow`.

numeric
-------

The numeric value type provides operators for ``>=``, ``<=``, ``>``, ``<``, ``is``, and ``is not``.

.. code-block:: python

    {
        'data_source': 'Number Scoops',
        'operator': '>=',
        'value': 3,
    }

string
------

Data sources marked a supporting the string value type can use the ``is``, ``is not``, ``contains``, ``starts with``, ``more than __ words``, and ``fewer than __ words`` operators.

.. code-block:: python

    {
        'data_source': "Scooper's Name",
        'operator': 'more than __ words',
        'value': 3,
    },
    {
        'data_source': "Scooper's Name",
        'operator': 'contains',
        'value': 'Heidi',
    }


collection
----------

To use the collection operators, a data source will usually need to provide a list of picklist_options to the client. It's fine to include those directly on the data source object:

.. code-block:: python

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
         ]
    }

Collections have access to ``any of`` and ``not any of`` operators.

.. code-block:: python

    {
        'data_source': 'Flavor',
        'operator': 'any of',
        'value': ['Strawberry', 'Chocolate'],
    }

Datetime Operators
--------------

Datetime operators are broken down into two sets, relative and absolute. Most timestamp sources will want to support both.

absolute_date
^^^^^^^^^^^^^

Absolute date values are ISO8601 strings, like ``"2017-03-22T18:14:30"``. The supported operators are ``before`` and ``after``.

.. code-block:: python

    {
        'data_source': 'Purchase Date',
        'operator': 'after',
        'value': '2017-03-22T18:14:30',
    }

relative_date
^^^^^^^^^^^^^

Relative date values are also strings, but they're things like ``"last_30_days"`` and ``"current_month"``. I'm not very happy with how these are designed, so they will likely change in a future version. Please let me know if you have any advice. Maybe there's already a standard way to refer to intervals of time that aren't anchored to a particular day?

.. code-block:: python

    {
        'data_source': 'Purchase Date',
        'operator': 'within',
        'value': 'last_7_days',
    }

The list of available values is found in `relative_dates.py <https://github.com/bgschiller/winnow/blob/master/winnow/relative_dates.py>`_.
