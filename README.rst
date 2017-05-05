Winnow
======

Winnow is a framework for server-side filtering of data. It is designed to be expressive, extensible, and fast. Winnow's inputs look something like this:

.. code-block:: json

    {
        "logical_op": "&",
        "filter_clauses": [
            {
                "data_source": "Created",
                "operator": "before",
                "value": "2015-03-01"
            },
            {
                "data_source": "Owner",
                "operator": "any of",
                "value": [
                    {"name": "Steven", "id": 23},
                    {"name": "Margaret", "id": 41},
                    {"name": "Evan", "id": 90}
                ]
            }
        ]
    }

Winnow's outputs look something like this:

.. code-block:: python

    "WHERE created_date < %s::timestamp AND owner_id = ANY(VALUES (%s),(%s),(%s))",
    ('2015-03-01', 23, 41, 90)
