"""A Slack bot using the real-time messaging API."""

from itertools import count
import json
import logging
from random import randint
from textwrap import dedent

import aiohttp
from aiohttp import MsgType

from .slack_api import SlackApiError, SlackBotApi

logger = logging.getLogger(__name__)


class SlackBot:
    """Base class Slack bot."""

    API_AUTH_ENDPOINT = 'auth.test'
    """Test endpoint for API authorisation."""

    MESSAGE_FILTERS = {}
    """Default filters for incoming messages."""

    INSTRUCTIONS = dedent("""
    These are the default instructions for an aSlack bot ({aslack_url}).

    Override these as appropriate for your specific needs.

    Hassle <@{owner_id}> if you need more help or information.
    """).format(
        aslack_url='https://github.com/textbook/aslack',
        owner_id='U0EVC55NX',
    )

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
        self.address_as = '<@{}>: '.format(id_)
        self._msg_ids = count(randint(1, 1000))

    async def join_rtm(self, filters=None):
        """Join the real-time messaging service.

        Arguments:
          filters (dict, optional): Dictionary mapping message filters
            to the functions they should dispatch to. Use an
            OrderedDict if precedence is important; only one filter,
            the first match, will be applied to each message.

        """
        if filters is None:
            filters = self.MESSAGE_FILTERS
        url = await self._get_socket_url()
        logger.debug('Connecting to {!r}'.format(url))
        async with aiohttp.ws_connect(url) as socket:
            first_msg = await socket.receive()
            self._validate_first_message(first_msg)
            async for message in socket:
                if message.tp == aiohttp.MsgType.text:
                    result = self._handle_message(message, filters)
                    if result is not None:
                        socket.send_str(result)
                elif message.tp in (MsgType.closed, MsgType.error):
                    if not socket.closed:
                        await socket.close()
                    break
        logger.info('Left real-time messaging.')

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

    def _format_message(self, channel, text):
        """Format an outoging message for transmission.

        Notes:
          Adds the message type ('message') and incremental ID.

        Arguments:
          channel (str): The channel to send to.
          text (str): The message text to send.

        Returns:
          str: The JSON string of the message.

        """
        payload = {'type': 'message', 'id': next(self._msg_ids)}
        payload.update(channel=channel, text=text)
        return json.dumps(payload)

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

    def _handle_message(self, message, filters):
        """Handle an incoming message appropriately.

        Arguments:
          message (aiohttp.Message): The incoming message to handle.
          filters (dict): The filters to apply to incoming messages.

        Returns:
          str: The response to send as a result.

        """
        data = self._unpack_message(message)
        logger.debug(data)
        if data.get('type') == 'error':
            raise SlackApiError(
                data.get('error', {}).get('msg', str(data))
            )
        for filter_, dispatch in filters.items():
            if filter_(data):
                logger.debug('Response triggered')
                return self._format_message(**dispatch(data))

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

        Raises:
          AttributeError: If there is no data attribute.
          json.JSONDecodeError: If the data isn't valid JSON.

        """
        return json.loads(msg.data)
