#!/usr/bin/env python

from distutils.core import setup

setup(name='csvvalidator',
      version='1.0',
      author='Alistair Miles',
      author_email='alimanfoo@googlemail.com',
      url='https://github.com/alimanfoo/csvvalidator',
      py_modules=['csvvalidator'],
      description='A simple library for validating data contained in CSV files or similar row-oriented data sources.',
      long_description=open('README.txt').read()
      )