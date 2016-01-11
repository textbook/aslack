"""A Slack bot using the real-time messaging API."""

from itertools import count
import json
import logging
from random import randint
from textwrap import dedent

from aiohttp import MsgType, ws_connect

from . import __name__ as mod_name, __version__
from .slack_api import SlackApiError, SlackBotApi
from .utils import truncate

logger = logging.getLogger(__name__)


class SlackBot:
    """Base class Slack bot.

    Arguments:
      id_ (:py:class:`str`): The bot's Slack ID.
      user (:py:class:`str`): The bot's friendly name.
      api (:py:class:`SlackApi`): The Slack API wrapper.

    Attributes:
      address_as (:py:class:`str`): The text that appears at the
        start of messages addressed to this bot (e.g.
        ``'<@user>: '``).
      full_name (:py:class:`str`): The name of the bot as it
        appears in messages about the bot (e.g. ``'<@user>'``).
      API_AUTH_ENDPOINT (:py:class:`str`): Test endpoint for API
        authorisation.
      INSTRUCTIONS (:py:class:`str`): Message to give the user when
        they request instructions.
      MESSAGE_FILTERS (:py:class:`dict`): Default filters for
        incoming messages
      RTM_HANDSHAKE (:py:class:`dict`): Expected handshake message
        from RTM API.
      RTM_START_ENDPOINT (:py:class:`str`): Start endpoint for
        real-time messaging.
      VERSION (:py:class:`str`): Version string to show to the user (if
        not overridden, will show the aSlack version).

    """

    API_AUTH_ENDPOINT = 'auth.test'

    INSTRUCTIONS = dedent("""
    These are the default instructions for an aSlack bot.

    Override these as appropriate for your specific needs.
    """)

    MESSAGE_FILTERS = {}

    RTM_HANDSHAKE = {'type': 'hello'}

    RTM_START_ENDPOINT = 'rtm.start'

    VERSION = ' '.join((mod_name, __version__))

    def __init__(self, id_, user, api):
        self.id_ = id_
        self.user = user
        self.api = api
        self.full_name = '<@{}>'.format(id_)
        self.address_as = '{}: '.format(self.full_name)
        self._msg_ids = count(randint(1, 1000))

    async def get_socket_url(self):
        """Get the WebSocket URL for the RTM session.

        Warning:
          The URL expires if the session is not joined within 30
          seconds of the API call to the start endpoint.

        Returns:
          :py:class:`str`: The socket URL.

        """
        data = await self.api.execute_method(
            self.RTM_START_ENDPOINT,
            simple_latest=True,
            no_unreads=True,
        )
        return data['url']

    async def handle_message(self, message, filters):
        """Handle an incoming message appropriately.

        Arguments:
          message (:py:class:`aiohttp.websocket.Message`): The incoming
            message to handle.
          filters (:py:class:`dict`): The filters to apply to incoming
            messages.

        Returns:
          :py:class:`str`: The response to send as a result.

        """
        data = self._unpack_message(message)
        logger.debug(data)
        if data.get('type') == 'error':
            raise SlackApiError(
                data.get('error', {}).get('msg', str(data))
            )
        elif self.message_is_to_me(data):
            text = data['text'][len(self.address_as):].strip()
            if text == 'help':
                return self._format_message(
                    channel=data['channel'],
                    text=self._instruction_list(filters),
                )
            elif text == 'version':
                return self._format_message(
                    channel=data['channel'],
                    text=self.VERSION,
                )
        for filter_, dispatch in filters.items():
            if filter_(self, data):
                logger.debug('Response triggered')
                response = await dispatch(self, data)
                return self._format_message(**response)

    async def join_rtm(self, filters=None):
        """Join the real-time messaging service.

        Arguments:
          filters (:py:class:`dict`, optional): Dictionary mapping
            message filters to the functions they should dispatch to.
            Use a :py:class:`collections.OrderedDict` if precedence is
            important; only one filter, the first match, will be
            applied to each message.

        """
        if filters is None:
            filters = self.MESSAGE_FILTERS
        url = await self.get_socket_url()
        logger.debug('Connecting to %r', url)
        async with ws_connect(url) as socket:
            first_msg = await socket.receive()
            self._validate_first_message(first_msg)
            async for message in socket:
                if message.tp == MsgType.text:
                    result = await self.handle_message(message, filters)
                    if result is not None:
                        logger.info(
                            'Sending message: %r',
                            truncate(result, max_len=50),
                        )
                        socket.send_str(result)
                elif message.tp in (MsgType.closed, MsgType.error):
                    if not socket.closed:
                        await socket.close()
                    break
        logger.info('Left real-time messaging.')

    def message_mentions_me(self, data):
        """If you send a message that mentions me"""
        return (data.get('type') == 'message' and
                self.full_name in data.get('text', ''))

    def message_is_to_me(self, data):
        """If you send a message directly to me"""
        return (data.get('type') == 'message' and
                data.get('text', '').startswith(self.address_as))

    @classmethod
    async def from_api_token(cls, token=None, api_cls=SlackBotApi):
        """Create a new instance from the API token.

        Arguments:
          token (:py:class:`str`, optional): The bot's API token
            (defaults to ``None``, which means looking in the
            environment or taking user input).
          api_cls (:py:class:`type`, optional): The class to create
            as the ``api`` argument for API access (defaults to
            :py:class:`aslack.slack_api.SlackBotApi`).

        Returns:
          :py:class:`SlackBot`: The new instance.

        """
        api = api_cls(token)
        data = await api.execute_method(cls.API_AUTH_ENDPOINT)
        return cls(data['user_id'], data['user'], api)

    def _format_message(self, channel, text):
        """Format an outoging message for transmission.

        Note:
          Adds the message type (``'message'``) and incremental ID.

        Arguments:
          channel (:py:class:`str`): The channel to send to.
          text (:py:class:`str`): The message text to send.

        Returns:
          :py:class:`str`: The JSON string of the message.

        """
        payload = {'type': 'message', 'id': next(self._msg_ids)}
        payload.update(channel=channel, text=text)
        return json.dumps(payload)

    def _instruction_list(self, filters):
        """Generates the instructions for a bot and its filters.

        Note:
          The guidance for each filter is generated by combining the
          docstrings of the predicate filter and resulting dispatch
          function with a single space between. The class's
          :py:attr:`INSTRUCTIONS` and the default help command are
          added.

        Arguments:
          filters (:py:class:`dict`): The filters to apply to incoming
            messages.

        Returns:
          :py:class:`str`: The bot's instructions.

        """
        return '\n\n'.join([
            self.INSTRUCTIONS.strip(),
            '*Supported methods:*',
            'If you send "@{}: help" to me I reply with these '
            'instructions.'.format(self.user),
            'If you send "@{}: version" to me I reply with my current '
            'version.'.format(self.user),
        ] + [
            ' '.join((filter_.__doc__, dispatch.__doc__))
            for filter_, dispatch in filters.items()
        ])

    @classmethod
    def _validate_first_message(cls, msg):
        """Check the first message matches the expected handshake.

        Note:
          The handshake is provided as :py:attr:`RTM_HANDSHAKE`.

        Arguments:
          msg (:py:class:`aiohttp.Message`): The message to validate.

        Raises:
          :py:class:`SlackApiError`: If the data doesn't match the
            expected handshake.

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
          msg (:py:class:`aiohttp.websocket.Message`): The message to
            unpack.

        Returns:
          :py:class:`dict`: The loaded data.

        Raises:
          :py:class:`AttributeError`: If there is no data attribute.
          :py:class:`json.JSONDecodeError`: If the data isn't valid
            JSON.

        """
        return json.loads(msg.data)
