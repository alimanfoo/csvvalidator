"""
TODO
"""


VALUE_CHECK_FAILED = 1

MESSAGES = {
            VALUE_CHECK_FAILED: 'Value check failed.'
            }


class CSVValidator(object):
    """TODO doc me"""

    
    def __init__(self, field_names):
        self._field_names = field_names
        self._value_checks = []

        
    def add_value_check(self, field_name, value_check, 
                        code=VALUE_CHECK_FAILED, 
                        message=MESSAGES[VALUE_CHECK_FAILED],
                        modulus=1):
        """Add a value check function for the specified field."""

        assert field_name in self._field_names, 'Unexpected field name: %s' % field_name
        t = (field_name, value_check, code, message, modulus)
        self._value_checks.append(t)
        
        
    def validate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None):
        """Validate data from the given data source and return a tuple of problems."""
        
        return tuple(self.ivalidate(data_source, expect_header_row, ignore_lines, summarize, limit, context))
    
    
    def ivalidate(self, data_source, 
                 expect_header_row=True,
                 ignore_lines=0,
                 summarize=False,
                 limit=0,
                 context=None):
        """Validate data from the given data source and return a problem generator.
        
        Use this function rather than validate() if you expect a large number
        of problems.
        
        """
        
        for i, r in enumerate(data_source):
            if expect_header_row and i == ignore_lines:
                pass # this is the header row
            elif i >= ignore_lines:
                for p in self._apply_value_checks(i, r):
                    yield p
                    
                    
    def _apply_value_checks(self, i, r):
        for field_name, value_check, code, message, modulus in self._value_checks:
            if i % modulus == 0:
                fi = self._field_names.index(field_name)
                value = r[fi]
                try:
                    value_check(value)
                except ValueError:
                    yield {
                           'code': code,
                           'message': message,
                           'row': i + 1,
                           'col': fi + 1,
                           'field': field_name,
                           'value': value,
                           'record': tuple(r)
                           }
