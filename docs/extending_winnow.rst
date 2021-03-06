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

When searching recipes, it makes sense to ask for recipes that use *all of* a list of ingredients. We can accomplish that right now, but it's a bit awkward.

.. code-block json

    {
        "logical_op": "&",
        "filter_clauses": [
            {
                "data_source": "Ingredients",
                "operator": "any of",
                "value": ["Tomato"]
            },
            {
                "data_source": "Ingredients",
                "operator": "any of",
                "value": ["Basil"]
            },
            {
                "data_source": "Ingredients",
                "operator": "any of",
                "value": ["Mozzarella"],
            }
        ]
    }

That's pretty painful to write. If your UI mirrors our json structure, it could be difficult for users to discover how to create a filter like that. Let's create an operator to handle this case.

First, we'll need to make a value type. We could piggyback on the 'collection' value type, but other collections don't necessarily know how to handle an 'all of' operator. For example, imagine we had a data source that was a star rating between 1 and 5. It wouldn't make sense to say "Rating is all of [3, 4]". By making a specific value type, we can allow each data source to decide whether or not to permit this operator. Let's call it 'collection_all'.

Now we'll add the operator to Winnow's list.

.. code-block python

    class RecipeWinnow(Winnow):

        operators = Winnow.operators + [
            {
                'name': 'all of',
                'value_type': 'collection_all',
                'negative': False
            },
        ]

We'll also need to specify that the Ingredients data_source supports 'collection_all'.

.. code-block :: json

    // source definition
    {
       "display_name": "Ingredients",
       "value_types": ["collection", "collection_all"]
    }

Finally, we need to provide instructions for building SQL to answer that query. Let's do that using a special case handler to begin with, but we'll revisit this decision in the next section.

.. code-block :: python

    @RecipeWinnow.special_case('Ingredients', 'collection_all')
    def ingredients(rw, clause):
        return rw.sql.prepare_query(
            '''
            id = ANY(
                {% for val in value %}
                    (SELECT recipe_id FROM ingredient
                     WHERE ingredient_text = {{ val }})
                    {% if not loop.last %}
                        INTERSECT
                    {% endif %}
                {% endfor %}
            )
            ''',
            value=clause['value_vivified'],
        )

That's it! Now we can make queries like

.. code-block :: json

    {
        "logical_op": "&",
        "filter_clauses": [
            {
                "data_source": "Ingredients",
                "operator": "all of",
                "value": ["Tomato", "Basil", "Mozzarella"]
            }
        ]
    }

to produce SQL like

.. code-block :: sql

    id = ANY(

        (SELECT recipe_id FROM ingredient
         WHERE ingredient_text = 'Tomato')
            INTERSECT
        (SELECT recipe_id FROM ingredient
         WHERE ingredient_text = 'Basil')
            INTERSECT
        (SELECT recipe_id FROM ingredient
         WHERE ingredient_text = 'Mozzarella')

    )

Including more data sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the last section, we said we would revisit the decision to use a special case handler. Well, that time has come! We have another data source where the 'all of' operator makes sense, and that's 'Suitable for Diet'. Our users are clamoring to be able to find recipes that are both gluten-free *and* vegetarian.

Now, for only two data sources, I would probably just use two special case handlers. But it's instructive to see how we might do things with 3, 4, 5, or more data sources. And since this *is* the documentation...

Let's override the definition of ``Winnow.where_clause``

.. code-block :: python

    class RecipeWinnow(Winnow):

        def where_clause(self, data_source, operator, value):
            if op['value_type'] == 'collection_all':
                return self.collection_all_of(data_source, operator, value):
            return super().where_clause(data_source, operator, value)

        def collection_all_of(self, data_source, operator, value):
            return self.prepare_query(
                '''
                id = ANY(
                    {% for val in values %}
                        (SELECT {{ foreign_key | sqlsafe }}
                         FROM {{ foreign_table | sqlsafe }}
                         WHERE {{ column | sqlsafe }} = {{ val }})
                        {% if not loop.last %} INTERSECT {% endif %}
                    {% endfor %}
                )''',
                values=value,
                foreign_key=data_source['foreign_key'],
                foreign_table=data_source['foreign_table'],
                column=data_source['column'],
            )

Notice that there's a few more pieces of information that we're expecting from ``data_source`` now: ``foreign_key``, ``foreign_table``, and ``column``. With 'Ingredients', all of this was just hard-coded. Now, since we want this to work for both 'Ingredients' and 'Suitable for Diet', we need to pass those values in as parameters. We'll store them on the data source:

.. code-block :: json

    // source definitions
    {
       "display_name": "Ingredients",
       "value_types": ["collection", "collection_all"],
       "foreign_table": "ingredient",
       "foreign_key": "recipe_id",
       "column": "ingredient_text",

    },
    {
       "display_name": "Suitable for Diet",
       "value_types": ["collection", "collection_all"],
       "picklist_values": ["vegan", "vegetarian", "gluten-free", "halal", "kosher"],
       "foreign_table": "diet_suitability",
       "foreign_key": "recipe_id",
       "column": "diet",
    }

.. 
.. Adding value types
.. ------------------
..
.. relative_to_date_field
.. ^^^^^^^^^^^^^^^^^^^^^^
.. This will allow us to say "Expected close Date before <any other date field>".
..
.. historical
.. ^^^^^^^^^^
..
.. Stage was 'Prospecting' as of <date>
..
.. Adding custom fields
.. --------------------
..
.. User-specific fields, generated dynamically
..
..
.. Replacing relative date handling
.. --------------------------------
..
.. "We want to start our year in February."
