#!/usr/bin/env python

from distutils.core import setup

setup(name='legis',
      version='0.1',
      description='legis dataset',
      author='Jessi Shank & Marianne Feng',
      author_email='jessishank1@gmail.com',
      # url='https://www.python.org/sigs/distutils-sig/',
      packages=['legis_data', 'legis_data.process'],
     )
