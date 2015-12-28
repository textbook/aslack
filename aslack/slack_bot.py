"""A Slack bot using the real-time messaging API."""

import logging

from .slack_api import SlackBotApi

logger = logging.getLogger(__name__)


class SlackBot:
    """Base class Slack bot."""

    API_AUTH_ENDPOINT = 'auth.test'
    """Test endpoint for API authorisation."""

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
