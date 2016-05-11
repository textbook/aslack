from json import dumps, loads
from os import environ

from atmdb import TMDbClient
import pytest

from examples.halliwell import Halliwell


if 'TMDB_API_TOKEN' in environ:

    @pytest.mark.asyncio
    async def test_halliwell_demo():
        query = '<@abc123>: actors in "Crank" and "Napoleon Dynamite"'
        message = type(
            'Message',
            (object,),
            {'data': dumps(dict(channel='hello', type='message', text=query))},
        )
        bot = Halliwell('abc123', '', None, tmdb_client=TMDbClient.from_env())
        result = await bot.handle_message(message, bot.MESSAGE_FILTERS)
        assert 'Efren Ramirez' in loads(result).get('text')
