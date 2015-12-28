"""Access to the base Slack Web API."""

import logging

import aiohttp

from .utils import get_api_token, FriendlyError, raise_for_status

logger = logging.getLogger(__name__)


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


class SlackApi:
    """Class to handle interaction with Slack's API."""

    API_BASE_URL = 'https://slack.com/api'
    """The base URL for Slack API calls."""

    API_METHODS = {
        'api': {'test': {'Checks API calling code.'}},
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
    """The API methods defined by Slack."""

    def __init__(self, token=None):
        if token is None:
            token = get_api_token()
        self.token = token

    async def execute_method(self, method, **params):
        """Execute a specified Slack Web API method.

        Notes:
          The API token is added automatically by this method.

        Arguments:
          method (str): The name of the method.
          **params (dict): Any additional parameters required.

        Returns:
          dict: The JSON data from the response.

        Raises:
          aiohttp.web_exceptions.HTTPException: If the HTTP request
            returns a code other than 200 (OK).
          SlackApiError: If the Slack API is reached but the response
           contains an error message.

        """
        url = self._create_url(method)
        params = params.copy()
        params['token'] = self.token
        logger.info('Executing method {!r}'.format(method))
        logger.debug('...with params {!r}'.format(params))
        response = await aiohttp.get(url, params=params)
        logger.info('Status: {}'.format(response.status))
        if response.status == 200:
            json = await response.json()
            logger.debug('...with JSON {!r}'.format(json))
            if json.get('ok'):
                return json
            raise SlackApiError(json['error'])
        else:
            raise_for_status(response)

    @classmethod
    def _create_url(cls, method):
        """Create the full API URL for a given method.

        Arguments:
          method (str): The name of the method.

        Returns:
          str: The full API URL.

        Raises:
          SlackApiError: If the method is unknown.

        """
        if not cls._method_exists(method):
            raise SlackApiError('The {!r} method is unknown.'.format(method))
        return '/'.join((cls.API_BASE_URL, method))

    @classmethod
    def _method_exists(cls, method):
        """Whether a given method exists in the known API.

        Notes:
          ``SlackApi`` and its subclasses provide a dictionary of
          ``API_METHODS``, a class attribute defining the known API.

        Arguments:
          method (str): The name of the method.

        Returns:
          bool: Whether the method is in the known API.

        """
        methods = cls.API_METHODS
        for key in method.split('.'):
            methods = methods.get(key)
            if methods is None:
                break
        if isinstance(methods, str):
            logger.debug('{!r}: {!r}'.format(method, methods))
            return True
        return False


class SlackBotApi(SlackApi):
    """API accessible to Slack custom bots."""

    API_METHODS = {
        'api': {'test': {'Checks API calling code.'}},
        'auth': {'test': 'Checks authentication & identity.'},
        'channels': {
            'history': 'Fetches history of messages and events from a channel.',
            'info': 'Gets information about a channel.',
            'list': 'Lists all channels in a Slack team.',
            'mark': 'Sets the read cursor in a channel.',
            'setPurpose': 'Sets the purpose for a channel.',
            'setTopic': 'Sets the topic for a channel.',
        },
        'chat': {
            'delete': 'Deletes a message.',
            'postMessage': 'Sends a message to a channel.',
            'update': 'Updates a message.'
        },
        'emoji': {'list': '	Lists custom emoji for a team.'},
        'files': {
            'delete': 'Deletes a file.',
            'upload': 'Uploads or creates a file.'
        },
        'groups': {
            'close': 'Closes a private channel.',
            'history': 'Fetches history of messages and events from a private '
                       'channel.',
            'info': 'Gets information about a private channel.',
            'list': 'Lists private channels that the calling user has access '
                    'to.',
            'mark': 'Sets the read cursor in a private channel.',
            'open': 'Opens a private channel.',
            'rename': 'Renames a private channel.',
            'setPurpose': 'Sets the purpose for a private channel.',
            'setTopic': 'Sets the topic for a private channel.',
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
            'remove': 'Un-pins an item from a channel.',
        },
        'reactions': {
            'add': 'Adds a reaction to an item.',
            'get': 'Gets reactions for an item.',
            'list': 'Lists reactions made by a user.',
            'remove': 'Removes a reaction from an item.',
        },
        'rtm': {'start': 'Starts a Real Time Messaging session.'},
        'stars': {
            'add': 'Adds a star to an item.',
            'remove': 'Removes a star from an item.',
        },
        'team': {'info': 'Gets information about the current team.'},
        'users': {
            'getPresence': 'Gets user presence information.',
            'info': 'Gets information about a user.',
            'list': 'Lists all users in a Slack team.',
            'setActive': 'Marks a user as active.',
            'setPresence': 'Manually sets user presence.',
        },
    }
    """The API methods defined by Slack."""


class SlackAppBotApi(SlackApi):
    """API accessible to Slack app bots."""

    API_METHODS = {
        'api': {'test': {'Checks API calling code.'}},
        'auth': {'test': 'Checks authentication & identity.'},
        'channels': {
            'info': 'Gets information about a channel.',
            'list': 'Lists all channels in a Slack team.',
        },
        'chat': {
            'delete': 'Deletes a message.',
            'postMessage': 'Sends a message to a channel.',
            'update': 'Updates a message.'
        },
        'files': {
            'delete': 'Deletes a file.',
            'upload': 'Uploads or creates a file.'
        },
        'groups': {
            'info': 'Gets information about a private channel.',
            'list': 'Lists private channels that the calling user has access '
                    'to.',
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
            'remove': 'Un-pins an item from a channel.',
        },
        'reactions': {
            'add': 'Adds a reaction to an item.',
            'get': 'Gets reactions for an item.',
            'list': 'Lists reactions made by a user.',
            'remove': 'Removes a reaction from an item.',
        },
        'rtm': {'start': 'Starts a Real Time Messaging session.'},
        'stars': {
            'add': 'Adds a star to an item.',
            'remove': 'Removes a star from an item.',
        },
        'users': {
            'getPresence': 'Gets user presence information.',
            'info': 'Gets information about a user.',
            'list': 'Lists all users in a Slack team.',
            'setActive': 'Marks a user as active.',
            'setPresence': 'Manually sets user presence.',
        },
    }
    """The API methods defined by Slack."""
