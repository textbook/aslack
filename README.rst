aSlack
======

*/əˈslæk/*

.. image:: https://img.shields.io/pypi/v/aslack.svg
    :target: https://pypi.python.org/pypi/aslack
    :alt: PyPI Version

.. image:: https://travis-ci.org/textbook/aslack.svg
    :target: https://travis-ci.org/textbook/aslack
    :alt: Travis Build Status

.. image:: https://coveralls.io/repos/textbook/aslack/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/textbook/aslack?branch=master
    :alt: Code Coverage

.. image:: https://www.quantifiedcode.com/api/v1/project/482551d8368740c68fb1d3e80c4f6664/badge.svg
    :target: https://www.quantifiedcode.com/app/project/482551d8368740c68fb1d3e80c4f6664
    :alt: Code Issues

.. image:: https://img.shields.io/badge/license-ISC-blue.svg
    :target: https://github.com/textbook/aslack/blob/master/LICENSE
    :alt: ISC License

aSlack is a lightweight, asynchronous wrapper for Slack's Web and Real-Time
Messaging (RTM) APIs, designed to allow the easy development of Slack tools and
bots in Python. It defines two principal components:

- ``SlackApi`` - a wrapper around the Web API; and
- ``SlackBot`` - a messaging bot built on top of the RTM API.

Compatibility
-------------

aSlack uses asyncio_ with the ``async`` and ``await`` syntax, so is only
compatible with Python versions 3.5 and above.

Dependencies
------------

Asynchronous HTTP and WebSocket functionality is provided by aiohttp_ (version
0.15 and above required for out-of-the-box WebSocket client support).

Documentation
-------------

aSlack's documentation is available on PythonHosted_.

Installation
------------

aSlack is available through the Python Package Index, PyPI_, you can install it
with::

    pip install aslack

Alternatively, clone or fork the repository and use e.g.::

    python setup.py develop

to install locally for development. In this case, you should also install the
development dependencies (ideally in a ``virtualenv``) using::

    pip install -r requirements.txt

Testing
-------

The test suite can be run using ``py.test`` directly or by running::

    python setup.py test

in which case ``pylint`` will also be run to check the code quality.

Additionally, a demo test for the Halliwell example can be run by setting the
environment variable ``TMDB_API_TOKEN``.

Examples
--------

See the ``/examples`` directory for examples of the kinds of bots that you can
build with aSlack.

Halliwell
.........

Based on both aSlack and `aTMDb`_, Halliwell is a bot that can provide
information on movies or actors and find overlaps. Two environment variables,
``SLACK_API_TOKEN`` and ``TMDB_API_TOKEN``, are required to run this example,
and configuration for easy deployment to Cloud Foundry is provided.

.. _aiohttp: http://aiohttp.rtfd.org/
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _aTMDb: http://pythonhosted.org/atmdb/
.. _PyPI: https://pypi.python.org/pypi
.. _PythonHosted: http://pythonhosted.org/aslack/