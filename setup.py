from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='pyfocus',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Operating System :: MacOS :: MacOS X",
          "Programming Language :: Python :: 2.7"
      ], 
      keywords='',
      author='Ian McCracken',
      author_email='ian.mccracken@gmail.com',
      url='http://github.com/iancmcc/pyfocus',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'appscript'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
