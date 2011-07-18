"""
TODO
"""


VALUE_CHECK_FAILED = 1
HEADER_CHECK_FAILED = 2

MESSAGES = {
            VALUE_CHECK_FAILED: 'Value check failed.',
            HEADER_CHECK_FAILED: 'Header check failed.'
            }


class CSVValidator(object):
    """TODO doc me"""

    
    def __init__(self, field_names):
        self._field_names = tuple(field_names)
        self._value_checks = []
        self._header_checks = []

        
    def add_value_check(self, field_name, value_check, 
                        code=VALUE_CHECK_FAILED, 
                        message=MESSAGES[VALUE_CHECK_FAILED],
                        modulus=1):
        """Add a value check function for the specified field."""

        assert field_name in self._field_names, 'Unexpected field name: %s' % field_name
        t = field_name, value_check, code, message, modulus
        self._value_checks.append(t)
        
        
    def add_header_check(self, 
                         code=HEADER_CHECK_FAILED, 
                         message=MESSAGES[HEADER_CHECK_FAILED]):
        """Add a header check."""
        
        t = code, message
        self._header_checks.append(t)
        
        
    def validate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None,
                 report_unexpected_errors=False):
        """Validate data from the given data source and return a tuple of problems."""
        
        return tuple(self.ivalidate(data_source, expect_header_row, ignore_lines, summarize, limit, context))
    
    
    def ivalidate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None,
                 report_unexpected_errors=False):
        """Validate data from the given data source and return a problem generator.
        
        Use this function rather than validate() if you expect a large number
        of problems.
        
        """
        
        for i, r in enumerate(data_source):
            if expect_header_row and i == ignore_lines:
                # r is the header row
                for p in self._apply_header_checks(i, r, summarize, report_unexpected_errors):
                    yield p
            elif i >= ignore_lines:
                # r is a data row
                for p in self._apply_value_checks(i, r, summarize, report_unexpected_errors):
                    yield p
                    
                    
    def _apply_value_checks(self, i, r, summarize, report_unexpected_errors):
        for field_name, value_check, code, message, modulus in self._value_checks:
            if i % modulus == 0: # support sampling
                fi = self._field_names.index(field_name)
                value = r[fi]
                try:
                    value_check(value)
                except ValueError:
                    p = {'code': code, 'message': message}
                    if not summarize:
                        p['row'] = i + 1
                        p['col'] = fi + 1
                        p['field'] = field_name
                        p['value'] = value
                        p['record'] = tuple(r)
                    yield p
                    
                    
    def _apply_header_checks(self, i, r, summarize, report_unexpected_errors):
        for code, message in self._header_checks:
            if tuple(r) != self._field_names:
                p = {'code': code, 'message': message}
                if not summarize:
                    p['row'] = i + 1
                    p['record'] = tuple(r)
                    p['missing'] = set(self._field_names) - set(r)
                    p['unexpected'] = set(r) - set(self._field_names) 
                yield p
