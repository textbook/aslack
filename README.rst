aSlack
======

*/əˈslæk/*

.. image:: https://img.shields.io/pypi/v/aslack.svg
    :target: https://pypi.python.org/pypi/aslack

.. image:: https://travis-ci.org/textbook/aslack.svg
    :target: https://travis-ci.org/textbook/aslack

.. image:: https://coveralls.io/repos/textbook/aslack/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/textbook/aslack?branch=master

.. image:: https://www.quantifiedcode.com/api/v1/project/482551d8368740c68fb1d3e80c4f6664/badge.svg
    :target: https://www.quantifiedcode.com/app/project/482551d8368740c68fb1d3e80c4f6664
    :alt: Code issues

.. image:: https://img.shields.io/badge/license-ISC-blue.svg
    :target: https://github.com/textbook/aslack/blob/master/LICENSE

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

Installation
------------

aSlack is available through the Python Package Index, PyPI_, you can install it
with::

    pip install aslack

Alternatively, download or clone this repository and use e.g.::

    python setup.py develop

to install locally for development. In this case, you should also install the
development dependencies using::

    pip install -r requirements.txt

.. _aiohttp: http://aiohttp.rtfd.org/
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _PyPI: https://pypi.python.org/pypi