.. Winnow documentation master file, created by
   sphinx-quickstart on Wed Mar 22 10:39:59 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the Winnow documentation
===================================

Winnow is a Python package for safely building SQL where clauses from untrusted user input. It's designed to be expressive, extensible, and fast. Winnow's inputs look something like this:

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

And its outputs looks like this:

.. code-block:: python

    (
      "WHERE created_date < %s::timestamp AND owner_id = ANY(VALUES (%s),(%s),(%s))",
      ('2015-03-01', 23, 41, 90)
    )


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   valuetypes



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
