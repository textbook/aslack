"""Core API wrapper functionality, adapted from `Flash Services`_.

.. _Flash Services:
    https://pypi.python.org/pypi/flash-services

"""
# pylint: disable=too-few-public-methods
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from os import getenv
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit


class Service(metaclass=ABCMeta):
    """Abstract base class for API wrapper services."""

    REQUIRED = set()
    """:py:class:`set`: The service's required configuration keys."""

    ROOT = ''
    """:py:class:`str`: The root URL for the API."""

    @abstractmethod
    def __init__(self, *_, **kwargs):
        self.service_name = kwargs.get('name')

    @property
    def headers(self):
        """Get the headers for the service requests.

        Returns:
          :py:class:`dict`: The header mapping.

        """
        return {}

    def url_builder(self, endpoint, *, root=None, params=None, url_params=None):
        """Create a URL for the specified endpoint.

        Arguments:
          endpoint (:py:class:`str`): The API endpoint to access.
          root: (:py:class:`str`, optional): The root URL for the
            service API.
          params: (:py:class:`dict`, optional): The values for format
            into the created URL (defaults to ``None``).
          url_params: (:py:class:`dict`, optional): Parameters to add
            to the end of the URL (defaults to ``None``).

        Returns:
          :py:class:`str`: The resulting URL.

        """
        if root is None:
            root = self.ROOT
        scheme, netloc, path, _, _ = urlsplit(root)
        return urlunsplit((
            scheme,
            netloc,
            urljoin(path, endpoint),
            urlencode(url_params or {}),
            '',
        )).format(**params or {})


class TokenAuthMixin:
    """Mix-in class for implementing token authentication.

    Arguments:
      api_token (:py:class:`str`): A valid API token.

    """

    TOKEN_ENV_VAR = None
    """:py:class:`str`: The environment variable holding the token."""

    def __init__(self, *, api_token, **kwargs):
        self.api_token = api_token
        super().__init__(**kwargs)

    @classmethod
    def from_env(cls):
        """Create a service instance from an environment variable."""
        token = getenv(cls.TOKEN_ENV_VAR)
        if token is None:
            msg = 'missing environment variable: {!r}'.format(cls.TOKEN_ENV_VAR)
            raise ValueError(msg)
        return cls(api_token=token)


class UrlParamMixin(TokenAuthMixin):
    """Mix-in class for implementing URL parameter authentication."""

    AUTH_PARAM = None
    """:py:class:`str`: The name of the URL parameter."""

    def url_builder(self, endpoint, params=None, url_params=None):
        """Add authentication URL parameter."""
        if url_params is None:
            url_params = OrderedDict()
        url_params[self.AUTH_PARAM] = self.api_token
        return super().url_builder(
            endpoint,
            params=params,
            url_params=url_params,
        )
