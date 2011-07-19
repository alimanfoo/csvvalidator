"""
TODO

"""


import re


UNEXPECTED_EXCEPTION = 0
VALUE_CHECK_FAILED = 1
HEADER_CHECK_FAILED = 2
RECORD_LENGTH_CHECK_FAILED = 3
VALUE_PREDICATE_FALSE = 4
RECORD_PREDICATE_FALSE = 5
UNIQUE_CHECK_FAILED = 6
ASSERT_CHECK_FAILED = 7
FINALLY_ASSERT_CHECK_FAILED = 7

MESSAGES = {
            UNEXPECTED_EXCEPTION: 'Unexpected exception [%s]: %s',
            VALUE_CHECK_FAILED: 'Value check failed.',
            HEADER_CHECK_FAILED: 'Header check failed.',
            RECORD_LENGTH_CHECK_FAILED: 'Record length check failed.',
            VALUE_PREDICATE_FALSE: 'Value predicate returned false.',
            RECORD_PREDICATE_FALSE: 'Record predicate returned false.',
            UNIQUE_CHECK_FAILED: 'Unique check failed.',
            ASSERT_CHECK_FAILED: 'Assertion check failed.',
            FINALLY_ASSERT_CHECK_FAILED: 'Final assertion check failed.'
            }


class CSVValidator(object):
    """TODO doc me"""

    
    def __init__(self, field_names):
        self._field_names = tuple(field_names)
        self._value_checks = []
        self._header_checks = []
        self._record_length_checks = []
        self._value_predicates = []
        self._record_predicates = []
        self._unique_checks = []

        
    def add_value_check(self, field_name, value_check, 
                        code=VALUE_CHECK_FAILED, 
                        message=MESSAGES[VALUE_CHECK_FAILED],
                        modulus=1):
        """Add a value check function for the specified field."""

        assert field_name in self._field_names, 'unexpected field name: %s' % field_name
        t = field_name, value_check, code, message, modulus
        self._value_checks.append(t)
        
        
    def add_header_check(self, 
                         code=HEADER_CHECK_FAILED, 
                         message=MESSAGES[HEADER_CHECK_FAILED]):
        """Add a header check."""
        
        t = code, message
        self._header_checks.append(t)
        
        
    def add_record_length_check(self,
                         code=RECORD_LENGTH_CHECK_FAILED, 
                         message=MESSAGES[RECORD_LENGTH_CHECK_FAILED],
                         modulus=1):
        """Add a record length check."""
        
        t = code, message, modulus
        self._record_length_checks.append(t)
        
        
    def add_value_predicate(self, field_name, value_predicate,
                        code=VALUE_PREDICATE_FALSE, 
                        message=MESSAGES[VALUE_PREDICATE_FALSE],
                        modulus=1):
        """Add a value predicate function for the specified field."""

        assert field_name in self._field_names, 'unexpected field name: %s' % field_name
        t = field_name, value_predicate, code, message, modulus
        self._value_predicates.append(t)
    
    
    def add_record_predicate(self, record_predicate,
                        code=RECORD_PREDICATE_FALSE, 
                        message=MESSAGES[RECORD_PREDICATE_FALSE],
                        modulus=1):
        """Add a record predicate function."""

        t = record_predicate, code, message, modulus
        self._record_predicates.append(t)
        
        
    def add_unique_check(self, key,
                        code=UNIQUE_CHECK_FAILED, 
                        message=MESSAGES[UNIQUE_CHECK_FAILED]):
        """Add a unique check on a single column or combination of columns."""
        
        if isinstance(key, basestring): 
            assert key in self._field_names, 'unexpected field name: %s' % key
        else:
            for f in key:
                assert f in self._field_names, 'unexpected field name: %s' % key
        t = key, code, message
        self._unique_checks.append(t)
    
    
    def validate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None,
                 report_unexpected_exceptions=True):
        """Validate data from the given data source and return a list of problems."""
        
        return list(self.ivalidate(data_source, expect_header_row, ignore_lines, summarize, limit, context, report_unexpected_exceptions))
    
    
    def ivalidate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None,
                 report_unexpected_exceptions=True):
        """Validate data from the given data source and return a problem generator.
        
        Use this function rather than validate() if you expect a large number
        of problems.
        
        """
        
        unique_sets = self._init_unique_sets() # used for unique checks
        for i, r in enumerate(data_source):
            if expect_header_row and i == ignore_lines:
                # r is the header row
                for p in self._apply_header_checks(i, r, summarize):
                    yield p
            elif i >= ignore_lines:
                # r is a data row
                for p in self._apply_each_methods(i, r, summarize, report_unexpected_exceptions):
                    yield p
                for p in self._apply_value_checks(i, r, summarize, report_unexpected_exceptions):
                    yield p
                for p in self._apply_record_length_checks(i, r, summarize):
                    yield p
                for p in self._apply_value_predicates(i, r, summarize, report_unexpected_exceptions):
                    yield p
                for p in self._apply_record_predicates(i, r, summarize, report_unexpected_exceptions):
                    yield p
                for p in self._apply_unique_checks(i, r, unique_sets, summarize):
                    yield p
                for p in self._apply_assert_methods(i, r, summarize, report_unexpected_exceptions):
                    yield p
        for p in self._apply_finally_assert_methods(summarize, report_unexpected_exceptions):
            yield p
                    
                    
    def _init_unique_sets(self):
        ks = dict()
        for t in self._unique_checks:
            key = t[0]
            ks[key] = set() # empty set
        return ks
                    
                    
    def _apply_value_checks(self, i, r, 
                            summarize=False, 
                            report_unexpected_exceptions=True):
        """Apply value check functions on the given record."""
        
        for field_name, value_check, code, message, modulus in self._value_checks:
            if i % modulus == 0: # support sampling
                fi = self._field_names.index(field_name)
                if fi < len(r): # only apply checks if there is a value
                    value = r[fi]
                    try:
                        value_check(value)
                    except ValueError:
                        p = {'code': code}
                        if not summarize:
                            p['message'] = message
                            p['row'] = i + 1
                            p['column'] = fi + 1
                            p['field'] = field_name
                            p['value'] = value
                            p['record'] = r
                        yield p
                    except Exception as e:
                        if report_unexpected_exceptions:
                            p = {'code': UNEXPECTED_EXCEPTION}
                            if not summarize:
                                p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                                p['row'] = i + 1
                                p['column'] = fi + 1
                                p['field'] = field_name
                                p['value'] = value
                                p['record'] = r
                                p['exception'] = e
                            yield p
                        
                    
    def _apply_header_checks(self, i, r, summarize=False):
        for code, message in self._header_checks:
            if tuple(r) != self._field_names:
                p = {'code': code}
                if not summarize:
                    p['message'] = message
                    p['row'] = i + 1
                    p['record'] = tuple(r)
                    p['missing'] = set(self._field_names) - set(r)
                    p['unexpected'] = set(r) - set(self._field_names) 
                yield p
                
                
    def _apply_record_length_checks(self, i, r, summarize=False):
        for code, message, modulus in self._record_length_checks:
            if i % modulus == 0: # support sampling
                if len(r) != len(self._field_names):
                    p = {'code': code}
                    if not summarize:
                        p['message'] = message
                        p['row'] = i + 1
                        p['record'] = r
                        p['length'] = len(r)
                    yield p
                
                
    def _apply_value_predicates(self, i, r, 
                                summarize=False, 
                                report_unexpected_exceptions=True):
        for field_name, value_predicate, code, message, modulus in self._value_predicates:
            if i % modulus == 0: # support sampling
                fi = self._field_names.index(field_name)
                if fi < len(r): # only apply predicate if there is a value
                    value = r[fi]
                    try:
                        valid = value_predicate(value)
                        if not valid:
                            p = {'code': code}
                            if not summarize:
                                p['message'] = message
                                p['row'] = i + 1
                                p['column'] = fi + 1
                                p['field'] = field_name
                                p['value'] = value
                                p['record'] = r
                            yield p
                    except Exception as e:
                        if report_unexpected_exceptions:
                            p = {'code': UNEXPECTED_EXCEPTION}
                            if not summarize:
                                p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                                p['row'] = i + 1
                                p['column'] = fi + 1
                                p['field'] = field_name
                                p['value'] = value
                                p['record'] = r
                                p['exception'] = e
                            yield p


    def _apply_record_predicates(self, i, r, 
                                 summarize=False, 
                                 report_unexpected_exceptions=True):
        for record_predicate, code, message, modulus in self._record_predicates:
            if i % modulus == 0: # support sampling
                rdict = self._as_dict(r)
                try:
                    valid = record_predicate(rdict)
                    if not valid:
                        p = {'code': code}
                        if not summarize:
                            p['message'] = message
                            p['row'] = i + 1
                            p['record'] = r
                        yield p
                except Exception as e:
                    if report_unexpected_exceptions:
                        p = {'code': UNEXPECTED_EXCEPTION}
                        if not summarize:
                            p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                            p['row'] = i + 1
                            p['record'] = r
                            p['exception'] = e
                        yield p
                    
                
    def _apply_unique_checks(self, i, r, unique_sets, 
                             summarize=False):
        for key, code, message in self._unique_checks:
            value = None
            values = unique_sets[key]
            if isinstance(key, basestring): # assume key is a field name
                fi = self._field_names.index(key)
                value = r[fi]
            else: # assume key is a list or tuple, i.e., compound key
                value = []
                for f in key:
                    fi = self._field_names.index(f)
                    value.append(r[fi])
                value = tuple(value) # enable hashing
            if value in values:
                p = {'code': code}
                if not summarize:
                    p['message'] = message
                    p['row'] = i + 1
                    p['record'] = r
                    p['key'] = key
                    p['value'] = value
                yield p
            values.add(value)


    def _apply_each_methods(self, i, r, 
                            summarize=False, 
                            report_unexpected_exceptions=True):
        for a in dir(self):
            if a.startswith('each'):
                rdict = self._as_dict(r)
                f = getattr(self, a)
                try:
                    f(i, rdict)
                except Exception as e:
                    if report_unexpected_exceptions:
                        p = {'code': UNEXPECTED_EXCEPTION}
                        if not summarize:
                            p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                            p['row'] = i + 1
                            p['record'] = r
                            p['exception'] = e
                        yield p

                    
    def _apply_assert_methods(self, i, r, 
                              summarize=False, 
                              report_unexpected_exceptions=True):
        for a in dir(self):
            if a.startswith('assert'):
                rdict = self._as_dict(r)
                f = getattr(self, a)
                try:
                    f(i, rdict)
                except AssertionError as e:
                    code = e.args[0] if len(e.args) > 0 else ASSERT_CHECK_FAILED
                    p = {'code': code}
                    if not summarize:
                        message = e.args[1] if len(e.args) > 1 else MESSAGES[ASSERT_CHECK_FAILED]
                        p['message'] = message
                        p['row'] = i + 1
                        p['record'] = r
                    yield p
                except Exception as e:
                    if report_unexpected_exceptions:
                        p = {'code': UNEXPECTED_EXCEPTION}
                        if not summarize:
                            p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                            p['row'] = i + 1
                            p['record'] = r
                            p['exception'] = e
                        yield p
    
    
    def _apply_finally_assert_methods(self, 
                                      summarize=False, 
                                      report_unexpected_exceptions=True):
        for a in dir(self):
            if a.startswith('finally_assert'):
                f = getattr(self, a)
                try:
                    f()
                except AssertionError as e:
                    code = e.args[0] if len(e.args) > 0 else FINALLY_ASSERT_CHECK_FAILED
                    p = {'code': code}
                    if not summarize:
                        message = e.args[1] if len(e.args) > 1 else MESSAGES[FINALLY_ASSERT_CHECK_FAILED]
                        p['message'] = message
                    yield p
                except Exception as e:
                    if report_unexpected_exceptions:
                        p = {'code': UNEXPECTED_EXCEPTION}
                        if not summarize:
                            p['message'] = MESSAGES[UNEXPECTED_EXCEPTION] % (e.__class__.__name__, e)
                            p['exception'] = e
                        yield p
    
    
    def _as_dict(self, r):
        """Convert the record to a dictionary using field names as keys."""
        d = dict()
        for i, f in enumerate(self._field_names):
            d[f] = r[i] if i < len(r) else None
        return d
    
    
def enumeration(*args):
    """
    Return a value check function which raises a value error if the value is not
    in a pre-defined enumeration of values.
    
    If you pass in a list, tuple or set as the single argument, it is assumed
    that the list/tuple/set defines the membership of the enumeration.
    
    If you pass in more than on argument, it is assumed the arguments themselves
    define the enumeration.
    
    """
    
    assert len(args) > 0, 'at least one argument is required'
    if len(args) == 1:
        # assume the first argument defines the membership
        members = args[0] 
    else:
        # assume the arguments are the members
        members = args 
    def checker(value):
        if value not in members:
            raise ValueError(value)
    return checker        
    
          
def match_pattern(regex):
    """
    TODO doc me
    
    """
    
    prog = re.compile(regex)
    def checker(v):
        result = prog.match(v)
        if result is None: 
            raise ValueError(v)
    return checker


def search_pattern(regex):
    """
    TODO doc me
    
    """
    
    prog = re.compile(regex)
    def checker(v):
        result = prog.search(v)
        if result is None: 
            raise ValueError(v)
    return checker


def number_range_inclusive(min, max, type=float):
    """
    TODO doc me
    
    """
    
    def checker(v):
        if type(v) < min or type(v) > max:
            raise ValueError(v)
    return checker


def number_range_exclusive(min, max, type=float):
    """
    TODO doc me
    
    """
    
    def checker(v):
        if type(v) <= min or type(v) >= max:
            raise ValueError(v)
    return checker


