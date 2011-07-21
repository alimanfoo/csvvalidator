#!/usr/bin/env python

"""
An executable Python script illustrating the use of the CSVValidator module.

This script illustrates some, but not all, of the features available. For a 
complete account of all features available, see the tests module.
"""

from csvvalidator import CSVValidator, enumeration, number_range_inclusive,\
    write_problems, datetime_string
import argparse
import os
import sys
import csv


def create_validator():
    """Create a CSV validator for patient demographic data."""

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
            raise ValueError(age_years, age_months)
    validator.add_record_check(check_age_variables,
                               'EX8', 'invalid age variables')
    
    return validator


def main():
    """Main function."""

    # define a command-line argument parser
    description = 'Validate a CSV data file.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('file', 
                        metavar='FILE', 
                        help='a file to be validated')
    parser.add_argument('-l', '--limit',
                        dest='limit',
                        type=int,
                        action='store',
                        default=0,
                        help='limit the number of problems reported'
                        )
    parser.add_argument('-s', '--summarize',
                        dest='summarize',
                        action='store_true',
                        default=False,
                        help='output only a summary of the different types of problem found'
                        )
    parser.add_argument('-e', '--report-unexpected-exceptions',
                        dest='report_unexpected_exceptions',
                        action='store_true',
                        default=False,
                        help='report any unexpected exceptions as problems'
                        )
    
    # parse arguments
    args = parser.parse_args()
    
    # sanity check arguments
    if not os.path.isfile(args.file):
        print '%s is not a file' % args.file
        sys.exit(1)

    with open(args.file, 'r') as f:

        # set up a csv reader for the data
        data_source = csv.reader(f, delimiter='\t')
        
        # create a validator
        validator = create_validator()
        
        # validate the data from the csv reader
        # N.B., validate() returns a list of problems;
        # if you expect a large number of problems, use ivalidate() instead
        # of validate(), but bear in mind that ivalidate() returns an iterator
        # so there is no len()
        problems = validator.validate(data_source, 
                                      summarize=args.summarize,
                                      report_unexpected_exceptions=args.report_unexpected_exceptions,
                                      context={'file': args.file})

        # write problems to stdout as restructured text
        write_problems(problems, sys.stdout, 
                       summarize=args.summarize, 
                       limit=args.limit)
        
        # decide how to exit
        if problems: # will not work with ivalidate() because it returns an iterator
            sys.exit(1)
        else:
            sys.exit(0)
    

if __name__ == "__main__":
    main()

