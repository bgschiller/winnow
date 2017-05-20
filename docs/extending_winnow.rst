.. _extending_winnow:

Extending Winnow
================

Winnow provides some basic functionality, but it's expected that you will sometimes need to extend it to accomplish your filtering goals.

Playing with the column definition
----------------------------------

Sometimes we need to do a little bit of processing to prepare data for filtering. In the `winnow-demo <https://github.com/bgschiller/winnow-demo>`_ project we're storing ``cook_time`` and ``prep_time`` as PostgreSQL interval columns, but we don't want to expect users to know how to enter a ISO 8601 formatted time interval. Instead, we'll define the source like this:

.. code-block :: json

    {
       "display_name": "Prep Time (minutes)",
       "column": "(EXTRACT(EPOCH FROM prep_time)::int / 60)",
       "value_types": ["numeric"]
    }

The ``column`` attribute of the source definition will be placed directly into the query without quoting, so we can use any valid SQL expression here -- not just the name of a column. A filter clause like

.. code-block :: json

    {
        "data_source": "Prep Time (minutes)",
        "operator": "<=",
        "value": 5
    }

will be turned into ``(((EXTRACT(EPOCH FROM prep_time)::int / 60) <= 5))``.

Referring to other tables
-------------------------

In the `winnow-demo <https://github.com/bgschiller/winnow-demo>`_ project, we are filtering recipes. We'd like to filter by ingredient, but the ingredients are stored in another table. The schema looks roughly like this.

.. image :: images/recipe_schema.png

By default, if we try to write a filter like

.. code-block :: json

    // source definition
    {
       "display_name": "Ingredients",
       "column": "ingredient",
       "value_types": ["collection"]
    }


    // filter clause
    {
        "data_source": "Ingredients",
        "operator": "any of",
        "value": ["Tomato"]
    }

it will produce SQL like ``WHERE ingredient IN ('Tomato')``. That won't work -- there's no column called ``ingredient``! Instead we'll have to override the handling of that data source.

.. code-block :: python


    @RecipeWinnow.special_case('Ingredients', 'collection')
    def ingredients(rw, clause):
        return rw.sql.prepare_query(
            '''
            {% if not_any_of %}
                NOT
            {% endif %}
            id = ANY(
                SELECT recipe_id FROM ingredient
                WHERE ingredient_text = ANY({{ value }})
            )
            ''',
            value=clause['value_vivified'],
            not_any_of=clause['operator'] == 'not any of',
        )

With this change, we get SQL like

.. code-block :: sql

    (
     id = ANY(
            SELECT recipe_id FROM ingredient
            WHERE ingredient_text = ANY(ARRAY['Tomato']))
    )

That will work much better! You can see an example of how this works in `recipe_winnow.py <https://github.com/bgschiller/winnow-demo/blob/master/winnow_demo/recipe_winnow.py>`_. The query is a bit more complicated there, because we're taking advantage of PostgreSQL's full-text-search capabilities. That way, a search for 'tomatoes' will also turn up results for 'tomato'.

Adding Operators
----------------

Adding value types
------------------

relative_to_date_field
^^^^^^^^^^^^^^^^^^^^^^
This will allow us to say "Expected close Date before <any other date field>".

historical
^^^^^^^^^^

Stage was 'Prospecting' as of <date>

Adding custom fields
--------------------

User-specific fields, generated dynamically


Replacing relative date handling
--------------------------------

"We want to start our year in February."
