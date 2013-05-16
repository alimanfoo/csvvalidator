"""
Tests for the `csvvalidator` module.

"""


import logging
import math

from csvvalidator import CSVValidator, VALUE_CHECK_FAILED, MESSAGES,\
    HEADER_CHECK_FAILED, RECORD_LENGTH_CHECK_FAILED, enumeration, match_pattern,\
    search_pattern, number_range_inclusive, number_range_exclusive,\
    VALUE_PREDICATE_FALSE, RECORD_PREDICATE_FALSE, UNIQUE_CHECK_FAILED,\
    ASSERT_CHECK_FAILED, UNEXPECTED_EXCEPTION, write_problems, datetime_string,\
    RECORD_CHECK_FAILED, datetime_range_inclusive, datetime_range_exclusive,\
    RecordError


# logging setup
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
debug, info, warning, error = logger.debug, logger.info, logger.warning, logger.error


def test_value_checks():
    """Some very simple tests of value checks."""

    # a simple validator to be tested
    field_names=('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('foo', int)
    validator.add_value_check('bar', float)

    # some test data
    data = (
            ('foo', 'bar'), # row 1 - header row
            ('12', '3.4'), # row 2 - valid
            ('1.2', '3.4'), # row 3 - foo invalid
            ('abc', '3.4'), # row 4 - foo invalid
            ('12', 'abc'), # row 5 - bar invalid
            ('', '3.4'), # row 6 - foo invalid (empty)
            ('12', ''), # row 7 - bar invalid (empty)
            ('abc', 'def') # row 8 - both invalid
            )

    # run the validator on the test data
    problems = validator.validate(data)

    assert len(problems) == 7

    # N.B., expect row and column indices start from 1

    problems_row2 = [p for p in problems if p['row'] == 2]
    assert len(problems_row2) == 0 # should be valid

    problems_row3 = [p for p in problems if p['row'] == 3]
    assert len(problems_row3) == 1
    p = problems_row3[0] # convenience variable
    assert p['column'] == 1 # report column index
    assert p['field'] == 'foo' # report field name
    assert p['code'] == VALUE_CHECK_FAILED # default problem code for value checks
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED] # default message
    assert p['value'] == '1.2' # report bad value
    assert p['record'] == ('1.2', '3.4') # report record

    problems_row4 = [p for p in problems if p['row'] == 4]
    assert len(problems_row4) == 1
    p = problems_row4[0] # convenience variable
    assert p['column'] == 1
    assert p['field'] == 'foo'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == 'abc'
    assert p['record'] == ('abc', '3.4')

    problems_row5 = [p for p in problems if p['row'] == 5]
    assert len(problems_row5) == 1
    p = problems_row5[0] # convenience variable
    assert p['column'] == 2
    assert p['field'] == 'bar'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == 'abc'
    assert p['record'] == ('12', 'abc')

    problems_row6 = [p for p in problems if p['row'] == 6]
    assert len(problems_row6) == 1
    p = problems_row6[0] # convenience variable
    assert p['column'] == 1
    assert p['field'] == 'foo'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == ''
    assert p['record'] == ('', '3.4')

    problems_row7 = [p for p in problems if p['row'] == 7]
    assert len(problems_row7) == 1
    p = problems_row7[0] # convenience variable
    assert p['column'] == 2
    assert p['field'] == 'bar'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == ''
    assert p['record'] == ('12', '')

    problems_row8 = [p for p in problems if p['row'] == 8]
    assert len(problems_row8) == 2 # expect both problems are found
    p0 = problems_row8[0] # convenience variable
    assert p0['column'] == 1
    assert p0['field'] == 'foo'
    assert p0['code'] == VALUE_CHECK_FAILED
    assert p0['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p0['value'] == 'abc'
    assert p0['record'] == ('abc', 'def')
    p1 = problems_row8[1] # convenience variable
    assert p1['column'] == 2
    assert p1['field'] == 'bar'
    assert p1['code'] == VALUE_CHECK_FAILED
    assert p1['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p1['value'] == 'def'
    assert p1['record'] == ('abc', 'def')


def test_header_check():
    """Test the header checks work."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_header_check() # use default code and message
    validator.add_header_check(code='X1', message='custom message') # provide custom code and message

    data = (
            ('foo', 'baz'),
            ('123', '456')
            )

    problems = validator.validate(data)
    assert len(problems) == 2

    p0 = problems[0]
    assert p0['code'] == HEADER_CHECK_FAILED
    assert p0['message'] == MESSAGES[HEADER_CHECK_FAILED]
    assert p0['record'] == ('foo', 'baz')
    assert p0['missing'] == set(['bar'])
    assert p0['unexpected'] == set(['baz'])
    assert p0['row'] == 1

    p1 = problems[1]
    assert p1['code'] == 'X1'
    assert p1['message'] == 'custom message'
    assert p1['missing'] == set(['bar'])
    assert p1['unexpected'] == set(['baz'])
    assert p1['record'] == ('foo', 'baz')
    assert p1['row'] == 1


def test_ignore_lines():
    """Test instructions to ignore lines works."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_header_check()
    validator.add_value_check('foo', int)
    validator.add_value_check('bar', float)

    data = (
            ('ignore', 'me', 'please'),
            ('ignore', 'me', 'too', 'please'),
            ('foo', 'baz'),
            ('1.2', 'abc')
            )

    problems = validator.validate(data, ignore_lines=2)
    assert len(problems) == 3

    header_problems = [p for p in problems if p['code'] == HEADER_CHECK_FAILED]
    assert len(header_problems) == 1
    assert header_problems[0]['row'] == 3

    value_problems = [p for p in problems if p['code'] == VALUE_CHECK_FAILED]
    assert len(value_problems) == 2
    for p in value_problems:
        assert p['row'] == 4


def test_record_length_checks():
    """Test the record length checks."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_record_length_check() # test default code and message
    validator.add_record_length_check('X2', 'custom message')

    data = (
            ('foo', 'bar'),
            ('12', '3.4'),
            ('12',), # be careful with syntax for singleton tuples
            ('12', '3.4', 'spong')
            )

    problems = validator.validate(data)
    assert len(problems) == 4, len(problems)

    # find problems reported under default code
    default_problems = [p for p in problems if p['code'] == RECORD_LENGTH_CHECK_FAILED]
    assert len(default_problems) == 2
    d0 = default_problems[0]
    assert d0['message'] == MESSAGES[RECORD_LENGTH_CHECK_FAILED]
    assert d0['row'] == 3
    assert d0['record'] == ('12',)
    assert d0['length'] == 1
    d1 = default_problems[1]
    assert d1['message'] == MESSAGES[RECORD_LENGTH_CHECK_FAILED]
    assert d1['row'] == 4
    assert d1['record'] == ('12', '3.4', 'spong')
    assert d1['length'] == 3

    # find problems reported under custom code
    custom_problems = [p for p in problems if p['code'] == 'X2']
    assert len(custom_problems) == 2
    c0 = custom_problems[0]
    assert c0['message'] == 'custom message'
    assert c0['row'] == 3
    assert c0['record'] == ('12',)
    assert c0['length'] == 1
    c1 = custom_problems[1]
    assert c1['message'] == 'custom message'
    assert c1['row'] == 4
    assert c1['record'] == ('12', '3.4', 'spong')
    assert c1['length'] == 3


def test_value_checks_with_missing_values():
    """
    Establish expected behaviour for value checks where there are missing values
    in the records.

    """

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('bar', float)

    data = (
            ('foo', 'bar'),
            ('12',) # this is missing value for bar, what happens to value check?
            )

    problems = validator.validate(data)

    # missing values are ignored - use record length checks to find these
    assert len(problems) == 0


def test_value_check_enumeration():
    """Test value checks with the enumeration() function."""

    field_names = ('foo', 'bar', 'baz')
    validator = CSVValidator(field_names)
    # define an enumeration directly with arguments
    validator.add_value_check('bar', enumeration('M', 'F'))
    # define an enumeration by passing in a list or tuple
    flavours = ('chocolate', 'vanilla', 'strawberry')
    validator.add_value_check('baz', enumeration(flavours))

    data = (
            ('foo', 'bar', 'baz'),
            ('1', 'M', 'chocolate'),
            ('2', 'F', 'maple pecan'),
            ('3', 'X', 'strawberry')
            )

    problems = validator.validate(data)
    assert len(problems) == 2

    p0 = problems[0]
    assert p0['code'] == VALUE_CHECK_FAILED
    assert p0['row'] == 3
    assert p0['column'] == 3
    assert p0['field'] == 'baz'
    assert p0['value'] == 'maple pecan'
    assert p0['record'] == ('2', 'F', 'maple pecan')

    p1 = problems[1]
    assert p1['code'] == VALUE_CHECK_FAILED
    assert p1['row'] == 4
    assert p1['column'] == 2
    assert p1['field'] == 'bar'
    assert p1['value'] == 'X'
    assert p1['record'] == ('3', 'X', 'strawberry')


def test_value_check_match_pattern():
    """Test value checks with the match_pattern() function."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('bar', match_pattern('\d{4}-\d{2}-\d{2}'))

    data = (
            ('foo', 'bar'),
            ('1', '1999-01-01'),
            ('2', 'abcd-ef-gh'),
            ('3', 'a1999-01-01'),
            ('4', '1999-01-01a') # this is valid - pattern attempts to match at beginning of line
            )

    problems = validator.validate(data)
    assert len(problems) == 2, len(problems)
    for p in problems:
        assert p['code'] == VALUE_CHECK_FAILED

    assert problems[0]['row'] == 3
    assert problems[1]['row'] == 4


def test_value_check_search_pattern():
    """Test value checks with the search_pattern() function."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('bar', search_pattern('\d{4}-\d{2}-\d{2}'))

    data = (
            ('foo', 'bar'),
            ('1', '1999-01-01'),
            ('2', 'abcd-ef-gh'),
            ('3', 'a1999-01-01'), # this is valid - pattern attempts to match anywhere in line
            ('4', '1999-01-01a') # this is valid - pattern attempts to match anywhere in line
            )

    problems = validator.validate(data)
    assert len(problems) == 1, len(problems)
    assert problems[0]['code'] == VALUE_CHECK_FAILED
    assert problems[0]['row'] == 3


def test_value_check_numeric_ranges():
    """Test value checks with numerical range functions."""

    field_names = ('foo', 'bar', 'baz', 'quux')
    validator = CSVValidator(field_names)
    validator.add_value_check('foo', number_range_inclusive(2, 6, int))
    validator.add_value_check('bar', number_range_exclusive(2, 6, int))
    validator.add_value_check('baz', number_range_inclusive(2.0, 6.3, float))
    validator.add_value_check('quux', number_range_exclusive(2.0, 6.3, float))

    data = (
            ('foo', 'bar', 'baz', 'quux'),
            ('2', '3', '2.0', '2.1'), # valid
            ('1', '3', '2.0', '2.1'), # foo invalid
            ('2', '2', '2.0', '2.1'), # bar invalid
            ('2', '3', '1.9', '2.1'), # baz invalid
            ('2', '3', '2.0', '2.0') # quux invalid
            )

    problems = validator.validate(data)
    assert len(problems) == 4, len(problems)
    for p in problems:
        assert p['code'] == VALUE_CHECK_FAILED

    assert problems[0]['row'] == 3 and problems[0]['field'] == 'foo'
    assert problems[1]['row'] == 4 and problems[1]['field'] == 'bar'
    assert problems[2]['row'] == 5 and problems[2]['field'] == 'baz'
    assert problems[3]['row'] == 6 and problems[3]['field'] == 'quux'


def test_value_checks_datetime():
    """Test value checks with datetimes."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('bar', datetime_string('%Y-%m-%d'))

    data = (
            ('foo', 'bar'),
            ('A', '1999-09-09'), # valid
            ('B', '1999-13-09'), # invalid month
            ('C', '1999-09-32'), # invalid day
            ('D', '1999-09-09ss') # invalid string
            )

    problems = validator.validate(data)
    assert len(problems) == 3, problems
    for p in problems:
        assert p['code'] == VALUE_CHECK_FAILED

    assert problems[0]['row'] == 3 and problems[0]['field'] == 'bar'
    assert problems[1]['row'] == 4 and problems[1]['field'] == 'bar'
    assert problems[2]['row'] == 5 and problems[2]['field'] == 'bar'


def test_value_checks_datetime_range():
    """Test value checks with datetime ranges."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_value_check('bar', datetime_range_inclusive('1999-09-09',
                                                              '2009-09-09',
                                                              '%Y-%m-%d'))
    validator.add_value_check('bar', datetime_range_exclusive('1999-09-09',
                                                              '2009-09-09',
                                                              '%Y-%m-%d'))

    data = (
            ('foo', 'bar'),
            ('A', '1999-09-10'), # valid
            ('B', '1999-09-09'), # invalid (exclusive)
            ('C', '2009-09-09'), # invalid (exclusive)
            ('D', '1999-09-08'), # invalid (both)
            ('E', '2009-09-10') # invalid (both)
            )

    problems = validator.validate(data)

    assert len(problems) == 6, len(problems)
    assert len([p for p in problems if p['row'] == 3]) == 1
    assert len([p for p in problems if p['row'] == 4]) == 1
    assert len([p for p in problems if p['row'] == 5]) == 2
    assert len([p for p in problems if p['row'] == 6]) == 2


def test_value_predicates():
    """Test the use of value predicates."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    foo_predicate = lambda v: math.pow(float(v), 2) < 64
    validator.add_value_predicate('foo', foo_predicate)
    bar_predicate = lambda v: math.sqrt(float(v)) > 8
    validator.add_value_predicate('bar', bar_predicate, 'X3', 'custom message')

    data = (
            ('foo', 'bar'),
            ('4', '81'), # valid
            ('9', '81'), # foo invalid
            ('4', '49') # bar invalid
            )

    problems = validator.validate(data)
    assert len(problems) == 2, len(problems)

    p0 = problems[0]
    assert p0['code'] == VALUE_PREDICATE_FALSE
    assert p0['message'] == MESSAGES[VALUE_PREDICATE_FALSE]
    assert p0['row'] == 3
    assert p0['column'] == 1
    assert p0['field'] == 'foo'
    assert p0['value'] == '9'
    assert p0['record'] == ('9', '81')

    p1 = problems[1]
    assert p1['code'] == 'X3'
    assert p1['message'] == 'custom message'
    assert p1['row'] == 4
    assert p1['column'] == 2
    assert p1['field'] == 'bar'
    assert p1['value'] == '49'
    assert p1['record'] == ('4', '49')


def test_record_checks():
    """Test the use of record checks."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    def foo_gt_bar(r):
        foo = int(r['foo'])
        bar = int(r['bar'])
        if foo < bar:
            raise RecordError
    validator.add_record_check(foo_gt_bar) # use default code and message

    def foo_gt_2bar(r):
        foo = int(r['foo'])
        bar = int(r['bar'])
        if foo < 2 * bar:
            raise RecordError('X4', 'custom message')
    validator.add_record_check(foo_gt_2bar)

    data = (
            ('foo', 'bar'),
            ('7', '3'), # valid
            ('5', '3'), # invalid - not foo_gt_2bar
            ('1', '3') # invalid - both predicates false
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 3, n

    row3_problems = [p for p in problems if p['row'] == 3]
    assert len(row3_problems) == 1
    p = row3_problems[0]
    assert p['code'] == 'X4'
    assert p['message'] == 'custom message'
    assert p['record'] == ('5', '3')

    row4_problems = [p for p in problems if p['row'] == 4]
    assert len(row4_problems) == 2

    row4_problems_default = [p for p in row4_problems if p['code'] == RECORD_CHECK_FAILED]
    assert len(row4_problems_default) == 1
    p = row4_problems_default[0]
    assert p['message'] == MESSAGES[RECORD_CHECK_FAILED]
    assert p['record'] == ('1', '3')

    row4_problems_custom = [p for p in row4_problems if p['code'] == 'X4']
    assert len(row4_problems_custom) == 1
    p = row4_problems_custom[0]
    assert p['message'] == 'custom message'
    assert p['record'] == ('1', '3')


def test_record_predicates():
    """Test the use of record predicates."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    def foo_gt_bar(r):
        return int(r['foo']) > int(r['bar']) # expect record will be a dictionary
    validator.add_record_predicate(foo_gt_bar) # use default code and message

    def foo_gt_2bar(r):
        return int(r['foo']) > 2 * int(r['bar'])
    validator.add_record_predicate(foo_gt_2bar, 'X4', 'custom message')

    data = (
            ('foo', 'bar'),
            ('7', '3'), # valid
            ('5', '3'), # invalid - not foo_gt_2bar
            ('1', '3') # invalid - both predicates false
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 3, n

    row3_problems = [p for p in problems if p['row'] == 3]
    assert len(row3_problems) == 1
    p = row3_problems[0]
    assert p['code'] == 'X4'
    assert p['message'] == 'custom message'
    assert p['record'] == ('5', '3')

    row4_problems = [p for p in problems if p['row'] == 4]
    assert len(row4_problems) == 2

    row4_problems_default = [p for p in row4_problems if p['code'] == RECORD_PREDICATE_FALSE]
    assert len(row4_problems_default) == 1
    p = row4_problems_default[0]
    assert p['message'] == MESSAGES[RECORD_PREDICATE_FALSE]
    assert p['record'] == ('1', '3')

    row4_problems_custom = [p for p in row4_problems if p['code'] == 'X4']
    assert len(row4_problems_custom) == 1
    p = row4_problems_custom[0]
    assert p['message'] == 'custom message'
    assert p['record'] == ('1', '3')


def test_unique_checks():
    """Test the uniqueness checks."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_unique_check('foo')

    data = (
            ('foo', 'bar'),
            ('1', 'A'),
            ('2', 'B'),
            ('1', 'C')
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['code'] == UNIQUE_CHECK_FAILED
    assert p['message'] == MESSAGES[UNIQUE_CHECK_FAILED]
    assert p['row'] == 4
    assert p['key'] == 'foo'
    assert p['value'] == '1'
    assert p['record'] == ('1', 'C')

def test_unique_checks_with_variable_record_lengths():
    """Test the uniqueness checks still work when record lengths vary."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_unique_check('bar')

    data = (
            ('foo', 'bar'),
            ('1', 'A'),
            ('2'),
            ('3', 'A')
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['code'] == UNIQUE_CHECK_FAILED
    assert p['message'] == MESSAGES[UNIQUE_CHECK_FAILED]
    assert p['row'] == 4
    assert p['key'] == 'bar'
    assert p['value'] == 'A'
    assert p['record'] == ('3', 'A')

def test_compound_unique_checks():
    """Test the uniqueness checks on compound keys."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_unique_check(('foo', 'bar'), 'X5', 'custom message')

    data = (
            ('foo', 'bar'),
            ('1', 'A'),
            ('2', 'B'),
            ('1', 'B'),
            ('2', 'A'),
            ('1', 'A')
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['code'] == 'X5'
    assert p['message'] == 'custom message'
    assert p['row'] == 6
    assert p['key'] == ('foo', 'bar')
    assert p['value'] == ('1', 'A')
    assert p['record'] == ('1', 'A')


def test_compound_unique_checks_with_variable_record_lengths():
    """Test the uniqueness checks on compound keys when record lengths vary."""

    field_names = ('something', 'foo', 'bar')
    validator = CSVValidator(field_names)
    validator.add_unique_check(('foo', 'bar'), 'X5', 'custom message')

    data = (
            ('something', 'foo', 'bar'),
            ('Z', '1', 'A'),
            ('Z', '2', 'B'),
            ('Z'),
            ('Z', '2', 'A'),
            ('Z', '1', 'A')
            )

    problems = validator.validate(data)
    print problems
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['code'] == 'X5'
    assert p['message'] == 'custom message'
    assert p['row'] == 6
    assert p['key'] == ('foo', 'bar')
    assert p['value'] == ('1', 'A')
    assert p['record'] == ('Z', '1', 'A')


def test_assert_methods():
    """Test use of 'assert' methods."""

    # define a custom validator class
    class MyValidator(CSVValidator):

        def __init__(self, threshold):
            field_names = ('foo', 'bar')
            super(MyValidator, self).__init__(field_names)
            self._threshold = threshold

        def assert_foo_plus_bar_gt_threshold(self, r):
            assert int(r['foo']) + int(r['bar']) > self._threshold # use default error code and message

        def assert_foo_times_bar_gt_threshold(self, r):
            assert int(r['foo']) * int(r['bar']) > self._threshold, ('X6', 'custom message')

    validator = MyValidator(42)

    data = (
            ('foo', 'bar'),
            ('33', '10'), # valid
            ('7', '8'), # invalid (foo + bar less than threshold)
            ('3', '4'), # invalid (both)
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 3, n

    row3_problems = [p for p in problems if p['row'] == 3]
    assert len(row3_problems) == 1
    p = row3_problems[0]
    assert p['code'] == ASSERT_CHECK_FAILED
    assert p['message'] == MESSAGES[ASSERT_CHECK_FAILED]
    assert p['record'] == ('7', '8')

    row4_problems = [p for p in problems if p['row'] == 4]
    assert len(row4_problems) == 2

    row4_problems_custom = [p for p in row4_problems if p['code'] == 'X6']
    assert len(row4_problems_custom) == 1, row4_problems
    p = row4_problems_custom[0]
    assert p['message'] == 'custom message'
    assert p['record'] == ('3', '4')

    row4_problems_default = [p for p in row4_problems if p['code'] == ASSERT_CHECK_FAILED]
    assert len(row4_problems_default) == 1
    p = row4_problems_default[0]
    assert p['message'] == MESSAGES[ASSERT_CHECK_FAILED]
    assert p['record'] == ('3', '4')


def test_check_methods():
    """Test use of 'check' methods."""

    # define a custom validator class
    class MyValidator(CSVValidator):

        def __init__(self, threshold):
            field_names = ('foo', 'bar')
            super(MyValidator, self).__init__(field_names)
            self._threshold = threshold

        def check_foo_plus_bar_gt_threshold(self, r):
            if int(r['foo']) + int(r['bar']) <= self._threshold:
                raise RecordError # use default error code and message

        def check_foo_times_bar_gt_threshold(self, r):
            if int(r['foo']) * int(r['bar']) <= self._threshold:
                raise RecordError('X6', 'custom message')

    validator = MyValidator(42)

    data = (
            ('foo', 'bar'),
            ('33', '10'), # valid
            ('7', '8'), # invalid (foo + bar less than threshold)
            ('3', '4'), # invalid (both)
            )

    problems = validator.validate(data)
    n = len(problems)
    assert n == 3, n

    row3_problems = [p for p in problems if p['row'] == 3]
    assert len(row3_problems) == 1
    p = row3_problems[0]
    assert p['code'] == RECORD_CHECK_FAILED
    assert p['message'] == MESSAGES[RECORD_CHECK_FAILED]
    assert p['record'] == ('7', '8')

    row4_problems = [p for p in problems if p['row'] == 4]
    assert len(row4_problems) == 2

    row4_problems_custom = [p for p in row4_problems if p['code'] == 'X6']
    assert len(row4_problems_custom) == 1
    p = row4_problems_custom[0]
    assert p['message'] == 'custom message'
    assert p['record'] == ('3', '4')

    row4_problems_default = [p for p in row4_problems if p['code'] == RECORD_CHECK_FAILED]
    assert len(row4_problems_default) == 1
    p = row4_problems_default[0]
    assert p['message'] == MESSAGES[RECORD_CHECK_FAILED]
    assert p['record'] == ('3', '4')


def test_each_and_finally_assert_methods():
    """Test 'each' and 'finally_assert' methods."""

    # define a custom validator class
    class MyValidator(CSVValidator):

        def __init__(self, threshold):
            field_names = ('foo', 'bar')
            super(MyValidator, self).__init__(field_names)
            self._threshold = threshold
            self._bars = []
            self._count = 0

        def each_store_bar(self, r):
            n = float(r['bar'])
            self._bars.append(n)
            self._count += 1

        def finally_assert_mean_bar_gt_threshold(self):
            mean = sum(self._bars) / self._count
            assert mean > self._threshold, ('X7', 'custom message')

    data = [
            ['foo', 'bar'],
            ['A', '2'],
            ['B', '3'],
            ['C', '7']
            ]

    validator = MyValidator(5.0)
    problems = validator.validate(data)
    assert len(problems) == 1
    p = problems[0]
    assert p['code'] == 'X7'
    assert p['message'] == 'custom message'

    data.append(['D', '10'])
    validator = MyValidator(5.0)
    problems = validator.validate(data)
    assert len(problems) == 0


def test_exception_handling():
    """Establish expectations for exception handling."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    validator.add_value_check('foo', int)

    def buggy_value_check(v):
        """I am a buggy value check."""
        raise Exception('something went wrong')
    validator.add_value_check('bar', buggy_value_check)

    def buggy_value_predicate(v):
        """I am a buggy value predicate."""
        raise Exception('something went wrong')
    validator.add_value_predicate('bar', buggy_value_predicate)

    def buggy_record_check(r):
        """I am a buggy record check."""
        raise Exception('something went wrong')
    validator.add_record_check(buggy_record_check)

    def buggy_record_predicate(r):
        """I am a buggy record predicate."""
        raise Exception('something went wrong')
    validator.add_record_predicate(buggy_record_predicate)

    def buggy_assert(r):
        """I am a buggy assert."""
        raise Exception('something went wrong')
    validator.assert_something_buggy = buggy_assert

    def buggy_check(r):
        """I am a buggy check."""
        raise Exception('something went wrong')
    validator.check_something_buggy = buggy_check

    def buggy_each(r):
        """I am a buggy each."""
        raise Exception('something went wrong')
    validator.each_something_buggy = buggy_each

    def buggy_finally_assert():
        """I am a buggy finally assert."""
        raise Exception('something went wrong')
    validator.finally_assert_something_buggy = buggy_finally_assert

    def buggy_skip(record):
        """I am a buggy skip."""
        raise Exception('something went wrong')
    validator.add_skip(buggy_skip)

    data = (
            ('foo', 'bar'),
            ('ab', '56')
            )

    problems = validator.validate(data, report_unexpected_exceptions=False)
    n = len(problems)
    assert n == 1, n
    p = problems[0]
    assert p['row'] == 2

    problems = validator.validate(data) # by default, exceptions are reported as problems
    n = len(problems)
    assert n == 10, n

    unexpected_problems = [p for p in problems if p['code'] == UNEXPECTED_EXCEPTION]
    assert len(unexpected_problems) == 9
    for p in unexpected_problems:
        e = p['exception']
        assert e.args[0] == 'something went wrong', e.args


def test_summarize():
    """Test use of summarize option."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    def foo_gt_bar(r):
        return int(r['foo']) > int(r['bar'])
    validator.add_record_predicate(foo_gt_bar)

    data = (
            ('foo', 'bar'),
            ('7', '3'), # valid
            ('1', '3') # invalid
            )

    problems = validator.validate(data, summarize=True)
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['code'] == RECORD_PREDICATE_FALSE
    for k in ('message', 'row', 'record'):
        assert k not in p


def test_limit():
    """Test the use of the limit option."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    def foo_gt_bar(r):
        return int(r['foo']) > int(r['bar'])
    validator.add_record_predicate(foo_gt_bar)

    data = (
            ('foo', 'bar'),
            ('7', '3'), # valid
            ('1', '3'), # invalid
            ('2', '3') # invalid
            )

    problems = validator.validate(data, limit=1)
    n = len(problems)
    assert n == 1, n

    problems = validator.validate(data)
    n = len(problems)
    assert n == 2, n


def test_context():
    """Test passing in of context information."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    def foo_gt_bar(r):
        return int(r['foo']) > int(r['bar'])
    validator.add_record_predicate(foo_gt_bar)

    data = (
            ('foo', 'bar'),
            ('7', '3'), # valid
            ('1', '3') # invalid
            )

    context = {'info': 'file X'}
    problems = validator.validate(data, context=context)
    n = len(problems)
    assert n == 1, n

    p = problems[0]
    assert p['context'] == context


def test_write_problems():
    """Test writing problems as restructured text."""

    class MockFile(object):

        def __init__(self):
            self.content = ''

        def write(self, s):
            self.content += s

    file = MockFile()

    problems = [
                {
                 'code': 'X1',
                 'message': 'invalid foo',
                 'row': 2,
                 'field': 'foo',
                 'context': {
                             'info': 'interesting'
                             }
                 },
                {
                 'code': 'X2',
                 'message': 'invalid bar',
                 'row': 3,
                 'field': 'bar',
                 'context': {
                             'info': 'very interesting'
                             }
                 }
                ]

    expectation = """
=================
Validation Report
=================

Problems
========

X1 - invalid foo
----------------
:field: foo
:row: 2
:info: interesting

X2 - invalid bar
----------------
:field: bar
:row: 3
:info: very interesting

Summary
=======

Found 2 problems in total.

:X1: 1
:X2: 1
"""

    write_problems(problems, file)
    assert file.content == expectation, file.content


def test_write_problems_summarize():
    """Test writing a problem summary as restructured text."""

    class MockFile(object):

        def __init__(self):
            self.content = ''

        def write(self, s):
            self.content += s

    file = MockFile()

    problems = [
                {
                 'code': 'X1',
                 'message': 'invalid foo',
                 'row': 2,
                 'field': 'foo',
                 'context': {
                             'info': 'interesting'
                             }
                },
                {
                 'code': 'X2',
                 'message': 'invalid bar',
                 'row': 3,
                 'field': 'bar',
                 'context': {
                             'info': 'very interesting'
                             }
                },
                {
                 'code': 'X2',
                 'message': 'invalid bar',
                 'row': 4,
                 'field': 'bar',
                 'context': {
                             'info': 'very very interesting'
                             }
                }
                ]

    expectation = """
=================
Validation Report
=================

Summary
=======

Found 3 problems in total.

:X1: 1
:X2: 2
"""

    write_problems(problems, file, summarize=True)
    assert file.content == expectation, file.content


def test_write_problems_with_limit():
    """Test writing problems with a limit as restructured text."""

    class MockFile(object):

        def __init__(self):
            self.content = ''

        def write(self, s):
            self.content += s

    file = MockFile()

    problems = [
                {
                 'code': 'X1',
                 'message': 'invalid foo',
                 'row': 2,
                 'field': 'foo',
                 'context': {
                             'info': 'interesting'
                             }
                 },
                {
                 'code': 'X2',
                 'message': 'invalid bar',
                 'row': 3,
                 'field': 'bar',
                 'context': {
                             'info': 'very interesting'
                             }
                 }
                ]

    expectation = """
=================
Validation Report
=================

Problems
========

X1 - invalid foo
----------------
:field: foo
:row: 2
:info: interesting

Summary
=======

Found at least 1 problem in total.

:X1: 1
"""

    write_problems(problems, file, limit=1)
    assert file.content == expectation, file.content


def test_skips():
    """Test skip functions."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)

    validator.add_record_length_check()
    validator.add_value_check('foo', int)

    def skip_pragma(record):
        return record[0].startswith('##')
    validator.add_skip(skip_pragma)

    data = (
            ('foo', 'bar'),
            ('1', 'X'),
            ('## this row', 'should be', 'skipped'),
            ('3', 'Y')
            )

    problems = validator.validate(data)
    assert len(problems) == 0, problems


def test_guard_conditions():
    """Test some guard conditions."""

    field_names = ('foo', 'bar')
    validator = CSVValidator(field_names)
    try:
        validator.add_value_check('foo', 'i am not callable')
    except AssertionError:
        pass # expected
    else:
        assert False, 'expected exception'


