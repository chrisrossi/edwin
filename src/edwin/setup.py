from setuptools import setup, find_packages
import sys, os

version = '0.1dev'

INSTALL_REQUIRES = [
    'Chameleon',
    'Paste',
    'PasteDeploy',
    'PIL',
    'simplejson',
]

TESTS_REQUIRE = [
    'nose',
    'coverage',
    'twill',
    'wsgi-intercept',
]

setup(name='edwin',
      version=version,
      description="",
      long_description='',
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=INSTALL_REQUIRES,
      tests_require=INSTALL_REQUIRES + ['nose', 'coverage'],
      test_suite='edwin',
      entry_points={
          'console_scripts': [
              'scan=edwin.scripts.scan:main',
              'debug=edwin.scripts.debug:main',
              'serve=edwin.application:main',
              ]
          }
      )
