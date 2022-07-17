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