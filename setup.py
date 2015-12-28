import io
import os
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

import aslack

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    author=aslack.__author__,
    author_email='mail@jonrshar.pe',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Communications :: Chat',
    ],
    cmdclass={'test': PyTest},
    description=aslack.__doc__,
    install_requires=['aiohttp>=0.15.0'],
    license='License :: OSI Approved :: ISC License (ISCL)',
    long_description=long_description,
    name='aslack',
    packages=['aslack'],
    platforms='any',
    tests_require=[
        'pytest',
        'asynctest',
        'pytest-asyncio',
    ],
    url='http://github.com/textbook/aslack/',
    version=aslack.__version__,
)