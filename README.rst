============
csvvalidator
============

This module provides some simple utilities for validating data contained in CSV 
files, or other similar data sources.

The source code for this module lives at: 

    https://github.com/alimanfoo/csvvalidator

Please report any bugs or feature requests via the issue tracker there.

Installation
============

This module is registered with the Python package index, so you can do::

    $ easy_install csvvalidator

... or download from http://pypi.python.org/pypi/csvvalidator and
install in the usual way::

    $ python setup.py install

If you want the bleeding edge, clone the source code repository::

    $ git clone git://github.com/alimanfoo/csvvalidator.git
    $ cd csvvalidator
    $ python setup.py install

Usage
=====

The `CSVValidator` class is the foundation for all validator objects that are 
capable of validating CSV data. 

You can use the CSVValidator class to dynamically construct a validator, e.g.::

    import sys
    import csv
    from csvvalidator import *

    field_names = (
                   'study_id', 
                   'patient_id', 
                   'gender', 
                   'age_years', 
                   'age_months',
                   'date_inclusion'
                   )

    validator = CSVValidator(field_names)
    
    # basic header and record length checks
    validator.add_header_check('EX1', 'bad header')
    validator.add_record_length_check('EX2', 'unexpected record length')
    
    # some simple value checks
    validator.add_value_check('study_id', int, 
                              'EX3', 'study id must be an integer')
    validator.add_value_check('patient_id', int, 
                              'EX4', 'patient id must be an integer')
    validator.add_value_check('gender', enumeration('M', 'F'), 
                              'EX5', 'invalid gender')
    validator.add_value_check('age_years', number_range_inclusive(0, 120, int), 
                              'EX6', 'invalid age in years')
    validator.add_value_check('date_inclusion', datetime_string('%Y-%m-%d'),
                              'EX7', 'invalid date')
    
    # a more complicated record check
    def check_age_variables(r):
        age_years = int(r['age_years'])
        age_months = int(r['age_months'])
        valid = (age_months >= age_years * 12 and 
                 age_months % age_years < 12)
        if not valid:
            raise RecordError('EX8', 'invalid age variables')
    validator.add_record_check(check_age_variables)

    # validate the data and write problems to stdout    
    data = csv.reader('/path/to/data.csv', delimiter='\t')
    problems = validator.validate(data)
    write_problems(problems, sys.stdout)

For more complex use cases you can also sub-class `CSVValidator` to define 
re-usable validator classes for specific data sources.

For a complete account of all of the functionality available from this module, 
see the example.py and tests.py modules in the source code repository.

Notes
=====

Note that the `csvvalidator` module is intended to be used in combination with 
the standard Python `csv` module. The `csvvalidator` module **will not** 
validate the *syntax* of a CSV file. Rather, the `csvvalidator` module can be 
used to validate any source of row-oriented data, such as is provided by a 
`csv.reader` object.

I.e., if you want to validate data from a CSV file, you have to first construct 
a CSV reader using the standard Python `csv` module, specifying the appropriate 
dialect, and then pass the CSV reader as the source of data to either the 
`CSVValidator.validate` or the `CSVValidator.ivalidate` method.

