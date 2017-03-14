#!/usr/bin/env python

from setuptools import setup
import ssl

setup(name='legis',
      version='0.1',
      description='legis dataset',
      author='Jessi Shank & Marianne Feng',
      author_email='jessishank1@gmail.com',
      # url='https://www.python.org/sigs/distutils-sig/',
      install_requires=[
        "Flask==0.12",
        "Flask-RESTful",
        "nltk",
        "requests-cache",
        "requests",
        "python-dateutil",

        ],
      packages=['legis_data', 'legis_data.process'],
     )
