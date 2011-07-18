"""
TODO
"""


import logging

from csvvalidator import *


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
    
    # N.B., expect row and col indices start from 1
    
    problems_row2 = [p for p in problems if p['row'] == 2] 
    assert len(problems_row2) == 0 # should be valid
    
    problems_row3 = [p for p in problems if p['row'] == 3]
    assert len(problems_row3) == 1
    p = problems_row3[0] # convenience variable 
    assert p['col'] == 1 # report column index
    assert p['field'] == 'foo' # report field name
    assert p['code'] == VALUE_CHECK_FAILED # default problem code for value checks
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED] # default message
    assert p['value'] == '1.2' # report bad value
    assert p['record'] == ('1.2', '3.4') # report record
    
    problems_row4 = [p for p in problems if p['row'] == 4]
    assert len(problems_row4) == 1
    p = problems_row4[0] # convenience variable
    assert p['col'] == 1
    assert p['field'] == 'foo'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == 'abc'
    assert p['record'] == ('abc', '3.4')
    
    problems_row5 = [p for p in problems if p['row'] == 5]
    assert len(problems_row5) == 1
    p = problems_row5[0] # convenience variable
    assert p['col'] == 2
    assert p['field'] == 'bar'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == 'abc'
    assert p['record'] == ('12', 'abc')    
    
    problems_row6 = [p for p in problems if p['row'] == 6]
    assert len(problems_row6) == 1
    p = problems_row6[0] # convenience variable
    assert p['col'] == 1
    assert p['field'] == 'foo'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == ''
    assert p['record'] == ('', '3.4')
    
    problems_row7 = [p for p in problems if p['row'] == 7]
    assert len(problems_row7) == 1
    p = problems_row7[0] # convenience variable
    assert p['col'] == 2
    assert p['field'] == 'bar'
    assert p['code'] == VALUE_CHECK_FAILED
    assert p['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p['value'] == ''
    assert p['record'] == ('12', '')    
    
    problems_row8 = [p for p in problems if p['row'] == 8]
    assert len(problems_row8) == 2 # expect both problems are found
    p0 = problems_row8[0] # convenience variable
    assert p0['col'] == 1
    assert p0['field'] == 'foo'
    assert p0['code'] == VALUE_CHECK_FAILED
    assert p0['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p0['value'] == 'abc'
    assert p0['record'] == ('abc', 'def')
    p1 = problems_row8[1] # convenience variable
    assert p1['col'] == 2
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
    assert p0['missing'] == {'bar'}
    assert p0['unexpected'] == {'baz'}
    assert p0['row'] == 1

    p1 = problems[1]
    assert p1['code'] == 'X1'
    assert p1['message'] == 'custom message'
    assert p1['missing'] == {'bar'}
    assert p1['unexpected'] == {'baz'}
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
    assert len(problems) == 0 # missing values are ignored - use record length checks
    
    
    