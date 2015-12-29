"""A Slack bot using the real-time messaging API."""

import logging
import json

import aiohttp

from .slack_api import SlackApiError, SlackBotApi

logger = logging.getLogger(__name__)


class SlackBot:
    """Base class Slack bot."""

    API_AUTH_ENDPOINT = 'auth.test'
    """Test endpoint for API authorisation."""

    RTM_HANDSHAKE = {'type': 'hello'}
    """Expected handshake message from RTM API."""

    RTM_START_ENDPOINT = 'rtm.start'
    """Start endpoint for real-time messaging."""

    def __init__(self, id_, user, api):
        """Initialise the new bot.

        Arguments:
          id_ (str): The bot's Slack ID.
          user (str): The bot's friendly name.
          api (SlackApi): The Slack API wrapper.

        """
        self.id_ = id_
        self.user = user
        self.api = api

    async def join_rtm(self):
        """Join the real-time messaging service."""
        async with aiohttp.ws_connect(await self._get_socket_url()) as socket:
            first_msg = await socket.receive()
            self._validate_first_message(first_msg)

    @classmethod
    def _validate_first_message(cls, msg):
        """Check the first message matches the expected handshake.

        Arguments:
          msg (aiohttp.Message): The message to validate.

        Raises:
          SlackApiError: If the data doesn't match the handshake.

        """
        data = cls._unpack_message(msg)
        logger.debug(data)
        if data != cls.RTM_HANDSHAKE:
            raise SlackApiError('Unexpected response: {!r}'.format(data))
        logger.info('Joined real-time messaging.')

    @staticmethod
    def _unpack_message(msg):
        """Unpack the data from the message.

        Arguments:
          msg (aiohttp.Message): The message to unpack.

        Returns:
          dict: The loaded data.

        """
        return json.loads(msg.data)

    async def _get_socket_url(self):
        """Get the WebSocket URL for the RTM session.

        Notes:
          The URL expires if the session is not joined within 30
          seconds of the API call to the start endpoint.

        Returns:
          str: The socket URL.

        """
        data = await self.api.execute_method(self.RTM_START_ENDPOINT)
        return data['url']

    @classmethod
    async def from_api_token(cls, token):
        """Create a new instance from the API token.

        Arguments:
          token (str): The bot's API token.

        Returns:
          SlackBot: The new instance.

        """
        api = SlackBotApi(token)
        data = await api.execute_method(cls.API_AUTH_ENDPOINT)
        return cls(data['user_id'], data['user'], api)
