"""Utility functionality."""

from aiohttp import web_exceptions


class FriendlyError(Exception):
    """Exception with friendlier error messages.

      Notes:
        The ``err_msg`` is resolved in :py:attr:`EXPECTED_ERRORS`,
        or passed through as-is if not found there.

      Arguments:
        err_msg (:py:class:`str`): The error message to attempt to
          resolve.
        *args (:py:class:`tuple`): Any additional positional arguments.

    """

    EXPECTED_ERRORS = {}
    """Friendly messages for expected errors."""

    def __init__(self, err_msg, *args):
        super().__init__(self.EXPECTED_ERRORS.get(err_msg, err_msg), *args)


def raise_for_status(response):
    """Raise an appropriate error for a given response.

    Arguments:
      response (:py:class:`aiohttp.ClientResponse`): The API response.

    Raises:
      :py:class:`aiohttp.web_exceptions.HTTPException`: The appropriate
        error for the response's status.

    """
    for err_name in web_exceptions.__all__:
        err = getattr(web_exceptions, err_name)
        if err.status_code == response.status:
            payload = dict(
                headers=response.headers,
                reason=response.reason,
            )
            if issubclass(err, web_exceptions._HTTPMove):  # pylint: disable=protected-access
                raise err(response.headers['Location'], **payload)
            raise err(**payload)


def truncate(text, max_len=350, end='...'):
    """Truncate the supplied text for display.

    Arguments:
      text (:py:class:`str`): The text to truncate.
      max_len (:py:class:`int`, optional): The maximum length of the
        text before truncation (defaults to 350 characters).
      end (:py:class:`str`, optional): The ending to use to show that
        the text was truncated (defaults to ``'...'``).

    Returns:
      :py:class:`str`: The truncated text.

    """
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', maxsplit=1)[0] + end
