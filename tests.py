"""
TODO
"""


from csvvalidator import *


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
    p1 = problems_row8[0] # convenience variable
    assert p1['col'] == 1
    assert p1['field'] == 'foo'
    assert p1['code'] == VALUE_CHECK_FAILED
    assert p1['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p1['value'] == 'abc'
    assert p1['record'] == ('abc', 'def')
    p2 = problems_row8[1] # convenience variable
    assert p2['col'] == 2
    assert p2['field'] == 'bar'
    assert p2['code'] == VALUE_CHECK_FAILED
    assert p2['message'] == MESSAGES[VALUE_CHECK_FAILED]
    assert p2['value'] == 'def'
    assert p2['record'] == ('abc', 'def')
    
    
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
    assert problems[0]['code'] == HEADER_CHECK_FAILED
    assert problems[0]['message'] == MESSAGES[HEADER_CHECK_FAILED]
    assert problems[0]['record'] == ('foo', 'baz')
    assert problems[0]['missing'] == {'bar'}
    assert problems[0]['unexpected'] == {'baz'}
    assert problems[0]['row'] == 1
    assert problems[1]['code'] == 'X1'
    assert problems[1]['message'] == 'custom message'
    assert problems[1]['missing'] == {'bar'}
    assert problems[1]['unexpected'] == {'baz'}
    assert problems[1]['record'] == ('foo', 'baz')
    assert problems[1]['row'] == 1
    