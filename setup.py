#!/usr/bin/env python
import re
import os
import sys
import time
import unittest
import ConfigParser
import tempfile
from setuptools import setup, Command


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class PostgresTest(Command):
    """
    Run the tests on Postgres.
    """
    description = "Run tests on Postgresql"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with tempfile.NamedTemporaryFile(delete=False) as config:
            config.write(
                "[options]\n"
                "db_type = postgresql\n"
                "db_host = localhost\n"
                "db_port = 5432\n"
                "db_user = postgres\n"
                "broker_url = redis://localhost:6379/0\n"
                "backend_url = redis://localhost:6379/1\n"
            )

        os.environ['DB_NAME'] = 'test_' + str(int(time.time()))
        os.environ['TRYTOND_CONFIG'] = config.name

        from tests import suite

        test_result = unittest.TextTestRunner(verbosity=3).run(suite())

        if test_result.wasSuccessful():
            sys.exit(0)
        sys.exit(-1)


config = ConfigParser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

requires = [
    'wrapt',
    'celery',
]

MODULE2PREFIX = {}

MODULE = "async"
PREFIX = "openlabs"
for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        requires.append(
            '%s_%s >= %s.%s, < %s.%s' % (
                MODULE2PREFIX.get(dep, 'trytond'), dep,
                major_version, minor_version, major_version,
                minor_version + 1
            )
        )
requires.append(
    'trytond >= %s.%s, < %s.%s' % (
        major_version, minor_version, major_version, minor_version + 1
    )
)
setup(
    name='%s_%s' % (PREFIX, MODULE),
    version=info.get('version', '0.0.1'),
    description="Execute Tryton methods asynchronously",
    author="Openlabs Technologies and Consulting (P) Ltd.",
    author_email='info@openlabs.co.in',
    url='http://www.openlabs.co.in/',
    package_dir={
        'trytond_async': '.',
        'trytond.modules.%s' % MODULE: '.'
    },
    packages=[
        'trytond_async',    # Another package alias for easy import of task
        'trytond.modules.%s' % MODULE,
        'trytond.modules.%s.tests' % MODULE,
    ],
    package_data={
        'trytond.modules.%s' % MODULE: info.get('xml', []) +
        info.get('translation', []) +
        ['tryton.cfg', 'locale/*.po', 'tests/*.rst', 'reports/*.odt'] +
        ['view/*.xml'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Tryton',
        'Topic :: Office/Business',
    ],
    license='GPL-3',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    %s = trytond.modules.%s
    """ % (MODULE, MODULE),
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    cmdclass={
        'test': PostgresTest,
    }
)
