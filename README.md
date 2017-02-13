Winnow
------

Winnow is a framework for server-side filtering of data. It is designed to be expressive, extensible, and fast. Winnow's inputs look something like this:

```
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
```

Winnow's outputs look something like this:

```
"WHERE created_date < %s::timestamp AND owner_id = ANY(VALUES (%s),(%s),(%s))",
('2015-03-01', 23, 41, 90)
```

### SQL-Injection

SQL-injection is the elephant in the room. We are basically building queries with string concatenation, just like mom always warned us not to do. This could be fixed in a future release. In the meantime, we mitigate this risk by being clever about how we quote string literals.

PostgreSQL supports two types of quotes for string literals. One is the familiar `'single quotes'`, and the other uses `$$pairs of dollar signs$$`. The dollar-quoting also allows you to include a token between the dollar signs that start a literal, and the same token must appear between the dollar signs that end the literal; `$apple$ I can talk about how oranges cost $$ here, and it won't end my quote$apple$`.

Of course, if we always use `$apple$` to start and end string literals, then we are vulnerable to sql-injection to any attacker who knows that. Instead, we use a random string of 6 letters, different for each literal.
