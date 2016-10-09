"""Access to the base Slack Web API.

Attributes:
  ALL (:py:class:`object`): Marker for cases where all child methods
    should be deleted by :py:func:`api_subclass_factory`.

"""

from copy import deepcopy
import logging

import aiohttp

from .core import Service, UrlParamMixin
from .utils import FriendlyError, raise_for_status

logger = logging.getLogger(__name__)


ALL = object()


class SlackApiError(FriendlyError):
    """Wrapper exception for error messages in the response JSON."""

    EXPECTED_ERRORS = {
        'account_inactive': 'Authentication token is for a deleted user or '
                            'team.',
        'invalid_auth': 'Invalid authentication token.',
        'migration_in_progress': 'Team is being migrated between servers.',
        'not_authed': "No authentication token provided.",
    }
    """Friendly messages for expected Slack API errors."""


class SlackApi(UrlParamMixin, Service):
    """Class to handle interaction with Slack's API.

    Attributes:
      API_METHODS (:py:class:`dict`): The API methods defined by Slack.

    """

    API_METHODS = {
        'api': {'test': 'Checks API calling code.'},
        'auth': {'test': 'Checks authentication & identity.'},
        'channels': {
            'archive': 'Archives a channel.',
            'create': 'Creates a channel.',
            'history': 'Fetches history of messages and events from a channel.',
            'info': 'Gets information about a channel.',
            'invite': 'Invites a user to a channel.',
            'join': 'Joins a channel, creating it if needed.',
            'kick': 'Removes a user from a channel.',
            'leave': 'Leaves a channel.',
            'list': 'Lists all channels in a Slack team.',
            'mark': 'Sets the read cursor in a channel.',
            'rename': 'Renames a channel.',
            'setPurpose': 'Sets the purpose for a channel.',
            'setTopic': 'Sets the topic for a channel.',
            'unarchive': 'Unarchives a channel.',
        },
        'chat': {
            'delete': 'Deletes a message.',
            'postMessage': 'Sends a message to a channel.',
            'update': 'Updates a message.'
        },
        'emoji': {'list': '	Lists custom emoji for a team.'},
        'files': {
            'delete': 'Deletes a file.',
            'info': 'Gets information about a team file.',
            'list': 'Lists & filters team files.',
            'upload': 'Uploads or creates a file.'
        },
        'groups': {
            'archive': 'Archives a private channel.',
            'close': 'Closes a private channel.',
            'create': 'Creates a private private channel.',
            'createChild': 'Clones and archives a private channel.',
            'history': 'Fetches history of messages and events from a private '
                       'channel.',
            'info': 'Gets information about a private channel.',
            'invite': 'Invites a user to a private channel.',
            'kick': 'Removes a user from a private channel.',
            'leave': 'Leaves a private channel.',
            'list': 'Lists private channels that the calling user has access '
                    'to.',
            'mark': 'Sets the read cursor in a private channel.',
            'open': 'Opens a private channel.',
            'rename': 'Renames a private channel.',
            'setPurpose': 'Sets the purpose for a private channel.',
            'setTopic': 'Sets the topic for a private channel.',
            'unarchive': 'Unarchives a private channel.',
        },
        'im': {
            'close': 'Close a direct message channel.',
            'history': 'Fetches history of messages and events from direct '
                       'message channel.',
            'list': 'Lists direct message channels for the calling user.',
            'mark': 'Sets the read cursor in a direct message channel.',
            'open': 'Opens a direct message channel.',
        },
        'mpim': {
            'close': 'Closes a multiparty direct message channel.',
            'history': 'Fetches history of messages and events from a '
                       'multiparty direct message.',
            'list': 'Lists multiparty direct message channels for the calling '
                    'user.',
            'mark': 'Sets the read cursor in a multiparty direct message '
                    'channel.',
            'open': 'This method opens a multiparty direct message.',
        },
        'oauth': {
            'access': 'Exchanges a temporary OAuth code for an API token.'
        },
        'pins': {
            'add': 'Pins an item to a channel.',
            'list': 'Lists items pinned to a channel.',
            'remove': 'Un-pins an item from a channel.',
        },
        'reactions': {
            'add': 'Adds a reaction to an item.',
            'get': 'Gets reactions for an item.',
            'list': 'Lists reactions made by a user.',
            'remove': 'Removes a reaction from an item.',
        },
        'rtm': {'start': 'Starts a Real Time Messaging session.'},
        'search': {
            'all': 'Searches for messages and files matching a query.',
            'files': 'Searches for files matching a query.',
            'messages': 'Searches for messages matching a query.',
        },
        'stars': {
            'add': 'Adds a star to an item.',
            'list': 'Lists stars for a user.',
            'remove': 'Removes a star from an item.',
        },
        'team': {
            'accessLogs': 'Gets the access logs for the current team.',
            'info': 'Gets information about the current team.',
            'integrationLogs': 'Gets the integration logs for the current '
                               'team.',
        },
        'usergroups': {
            'create': 'Create a user group.',
            'disable': 'Disable an existing user group.',
            'enable': 'Enable a user group.',
            'list': 'List all user groups for a team.',
            'update': 'Update an existing user group',
            'users': {
                'list': 'List all users in a user group',
                'update': '	Update the list of users for a user group.',
            },
        },
        'users': {
            'getPresence': 'Gets user presence information.',
            'info': 'Gets information about a user.',
            'list': 'Lists all users in a Slack team.',
            'setActive': 'Marks a user as active.',
            'setPresence': 'Manually sets user presence.',
        },
    }

    AUTH_PARAM = 'token'

    REQUIRED = {'api_token'}

    ROOT = 'https://slack.com/api/'

    TOKEN_ENV_VAR = 'SLACK_API_TOKEN'

    async def execute_method(self, method, **params):
        """Execute a specified Slack Web API method.

        Arguments:
          method (:py:class:`str`): The name of the method.
          **params (:py:class:`dict`): Any additional parameters
            required.

        Returns:
          :py:class:`dict`: The JSON data from the response.

        Raises:
          :py:class:`aiohttp.web_exceptions.HTTPException`: If the HTTP
            request returns a code other than 200 (OK).
          SlackApiError: If the Slack API is reached but the response
           contains an error message.

        """
        url = self.url_builder(method, url_params=params)
        logger.info('Executing method %r', method)
        response = await aiohttp.get(url)
        logger.info('Status: %r', response.status)
        if response.status == 200:
            json = await response.json()
            logger.debug('...with JSON %r', json)
            if json.get('ok'):
                return json
            raise SlackApiError(json['error'])
        else:
            raise_for_status(response)

    @classmethod
    def method_exists(cls, method):
        """Whether a given method exists in the known API.

        Arguments:
          method (:py:class:`str`): The name of the method.

        Returns:
          :py:class:`bool`: Whether the method is in the known API.

        """
        methods = cls.API_METHODS
        for key in method.split('.'):
            methods = methods.get(key)
            if methods is None:
                break
        if isinstance(methods, str):
            logger.debug('%r: %r', method, methods)
            return True
        return False


def api_subclass_factory(name, docstring, remove_methods, base=SlackApi):
    """Create an API subclass with fewer methods than its base class.

    Arguments:
      name (:py:class:`str`): The name of the new class.
      docstring (:py:class:`str`): The docstring for the new class.
      remove_methods (:py:class:`dict`): The methods to remove from
        the base class's :py:attr:`API_METHODS` for the subclass. The
        key is the name of the root method (e.g. ``'auth'`` for
        ``'auth.test'``, the value is either a tuple of child method
        names (e.g. ``('test',)``) or, if all children should be
        removed, the special value :py:const:`ALL`.
      base (:py:class:`type`, optional): The base class (defaults to
        :py:class:`SlackApi`).

    Returns:
      :py:class:`type`: The new subclass.

    Raises:
      :py:class:`KeyError`: If the method wasn't in the superclass.

    """
    methods = deepcopy(base.API_METHODS)
    for parent, to_remove in remove_methods.items():
        if to_remove is ALL:
            del methods[parent]
        else:
            for method in to_remove:
                del methods[parent][method]
    return type(name, (base,), dict(API_METHODS=methods, __doc__=docstring))


SlackBotApi = api_subclass_factory(  # pylint: disable=invalid-name
    'SlackBotApi',
    'API accessible to Slack custom bots.',
    remove_methods=dict(
        channels=('archive', 'create', 'invite', 'join', 'kick', 'leave',
                  'rename', 'unarchive'),
        files=('info', 'list'),
        groups=('archive', 'create', 'createChild', 'invite', 'kick', 'leave',
                'rename', 'unarchive'),
        pins=('list',),
        search=ALL,
        stars=('list',),
        team=('accessLogs', 'integrationLogs'),
        usergroups=ALL,
    ),
)


SlackAppBotApi = api_subclass_factory(  # pylint: disable=invalid-name
    'SlackAppBotApi',
    'API accessible to Slack app bots.',
    remove_methods=dict(
        channels=('history', 'mark', 'setPurpose', 'setTopic'),
        emoji=ALL,
        groups=('close', 'history', 'mark', 'open', 'setPurpose', 'setTopic'),
        team=ALL,
    ),
    base=SlackBotApi,
)
