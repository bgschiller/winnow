from nose.tools import assert_equals

from templating import SqlFragment

def test_sqlfragments_can_be_composed():
    """
    Including a SqlFragment in a template includes all of it's
    parameters.
    """


a = SqlFragment('once upon a %s %s', ('midnight', 'dreary'))
b = SqlFragment(' while I pondered, %s and %s', ('weak', 'weary'))
c = SqlFragment(
    'Over many a %s and %s volume of %s lore,',
    ('quaint', 'curious', 'forgotten'))

def test_sqlfragments_can_by_concatenated():
    expected = SqlFragment(
        'once upon a %s %s while I pondered, %s and %s',
        ('midnight', 'dreary', 'weak', 'weary'))

    assert_equals(a + b, expected)

def test_sqlfragments_can_be_joined():
    result = SqlFragment.join('\n', (a, b, c))
    expected = SqlFragment(
        '''once upon a %s %s
 while I pondered, %s and %s
Over many a %s and %s volume of %s lore,''',
        ('midnight', 'dreary', 'weak', 'weary',
         'quaint', 'curious', 'forgotten'))

    assert_equals(result, expected)

def test_unpack_sqlfragment():
    pass
