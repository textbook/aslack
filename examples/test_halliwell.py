from json import dumps, loads
from os import environ
from unittest import mock

from atmdb import TMDbClient
import pytest

from examples.halliwell import Halliwell, ActorOverlapQueryHandler


def test_description():
    expected = ("If you send me a message asking 'actors in' with a quoted list"
                " of movies I will find movies featuring all of those actors.")
    assert ActorOverlapQueryHandler(None).description() == expected


if 'TMDB_API_TOKEN' in environ:

    @pytest.mark.asyncio
    async def test_halliwell_demo():
        query = '<@abc123>: actors in "Crank" and "Napoleon Dynamite"'
        message = type(
            'Message',
            (object,),
            {'data': dumps(dict(channel='hello', type='message', text=query))},
        )
        mock_socket = mock.MagicMock()
        bot = Halliwell('abc123', '', None, tmdb_client=TMDbClient.from_env())
        bot.socket = mock_socket
        await bot.handle_message(
            message,
            [cls(bot) for cls in bot.MESSAGE_FILTERS],
        )
        message = loads(mock_socket.send_str.call_args[0][0])
        assert 'Efren Ramirez' in message.get('text')
