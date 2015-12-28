"""Utility functionality."""

from aiohttp import web_exceptions

import os

API_TOKEN_ENV = 'SLACK_API_TOKEN'
"""The environment variable to store the user's API token in."""


class FriendlyError(Exception):
    """Exception with friendlier error messages."""

    EXPECTED_ERRORS = {}
    """Friendly messages for expected errors."""

    def __init__(self, err_msg, *args):
        super().__init__(self.EXPECTED_ERRORS.get(err_msg, err_msg), *args)


def raise_for_status(response):
    """Raise an appropriate error for a given response.

    Arguments:
      response (aiohttp.ClientResponse): The API response.

    Raises:
      aiohttp.web_exceptions.HTTPException: The appropriate error
        for the response's status.

    """
    for err_name in web_exceptions.__all__:
        err = getattr(web_exceptions, err_name)
        if err.status_code == response.status:
            payload = dict(
                headers=response.headers,
                reason=response.reason,
            )
            if issubclass(err, web_exceptions._HTTPMove):
                raise err(response.headers['Location'], **payload)
            raise err(**payload)


def get_api_token():
    """Allow the user to enter their API token."""
    token = os.getenv(API_TOKEN_ENV)
    if token:
        return token
    template = ('Enter your API token (this will be stored '
                'as {} for future use): ').format(API_TOKEN_ENV)
    token = input(template)
    os.environ[API_TOKEN_ENV] = token
    return token
