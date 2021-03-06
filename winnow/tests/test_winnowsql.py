import datetime

from nose.tools import assert_equals

from ..templating import jsonify
from ..templating import pg_null
from ..templating import PGJson
from ..templating import WinnowSql

sql = WinnowSql()



def test_datetimes_turn_to_timestamps():
    d = datetime.datetime(2017, 2, 22, 15, 23)
    query, params = sql.prepare_query(
        "SELECT {{ d }} + interval '1 day'",
        d=d)
    assert_equals(query, "SELECT %s::timestamp + interval '1 day'")
    assert_equals(params, [d])

def test_booleans_turn_to_bools():
    query, params = sql.prepare_query(
        "SELECT {{ t }}",
        t=True)
    assert_equals(query, "SELECT %s")
    assert_equals(params, [True])


def test_pg_null_includes_type():
    query, params = sql.prepare_query(
        'SELECT {{ int_null }}, {{ text_null }}',
        int_null=pg_null('int'),
        text_null=pg_null('text'))
    assert_equals(query, 'SELECT %s::int, %s::text')
    assert_equals(params, [None, None])

blobject = {
    'a':12,
    'b':[ 'c','d', 14],
    'date': datetime.datetime(2017, 2, 22, 15, 23)
}


def test_pg_json_produces_jsonb():
    query, params = sql.prepare_query(
        'SELECT {{ vals }}',
        vals=PGJson(blobject))
    assert_equals(query, 'SELECT %s::jsonb')
    assert_equals(params, [jsonify(blobject)])

def test_dicts_produce_jsonb():
    query, params = sql.prepare_query(
        'SELECT {{ vals }}',
        vals=blobject)
    assert_equals(query, 'SELECT %s::jsonb')
    assert_equals(params, [jsonify(blobject)])


def test_none_and_undefined_produce_null():
    query, params = sql.prepare_query(
        'SELECT {{ nada }}, {{ no_se }}',
        nada=None)
    assert_equals(query, 'SELECT %s, %s')
    assert_equals(params, [None, None])

def test_jsonify_works_on_dates():
    json_w_date = {'today': datetime.datetime(2017, 5, 18, 21, 30)}
    query, params = sql.prepare_query(
        'SELECT {{ json_w_date }}',
        json_w_date=json_w_date)
    assert_equals(query, 'SELECT %s::jsonb')
    assert_equals(params, [jsonify(json_w_date)])

def test_lists_create_arrays():
    query, params = sql.prepare_query(
        "SELECT 'apple' = ANY({{ vals }})",
        vals=['peach', 'coconut', 'banana'])
    assert_equals(query, "SELECT 'apple' = ANY(%s)")
    assert_equals(params, [['peach', 'coconut', 'banana']])

def test_sqlfragments_can_be_composed():
    """
    Including a SqlFragment in a template includes all of it's
    parameters.
    """
    servings_check = sql.prepare_query(
        'num_servings >= {{ people }}',
        people=12)
    time_check = sql.prepare_query(
        "cook_time <= interval ({{ max_time_in_minutes }} || ' minute')",
        max_time_in_minutes=100)
    recipe_requirements = sql.prepare_query(
        '{{ servings_check}} AND {{ time_check }}',
        servings_check=servings_check, time_check=time_check)
    assert_equals(
        recipe_requirements.query,
        "num_servings >= %s AND cook_time <= interval (%s || ' minute')")
    assert_equals(
        recipe_requirements.params,
        [12, 100])
