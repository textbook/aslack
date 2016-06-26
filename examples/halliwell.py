"""Example aSlack bot to give you information on movies."""
import re
from textwrap import dedent

import asyncio

from atmdb import TMDbClient
from atmdb.utils import find_overlapping_actors, find_overlapping_movies

from aslack.slack_bot import SlackBot, BotMessageHandler


QUOTED = re.compile(r'"([^"]+)"')
"""Regular expression to extract quoted text."""


class ActorOverlapQueryHandler(BotMessageHandler):
    """Handles queries about movies with the same group of actors.

      If you send me a message asking 'actors in' with a quoted list of
      movies I will find movies featuring all of those actors.

    """

    PHRASE = 'actors in'

    async def __anext__(self):
        if not self.text:
            raise StopAsyncIteration
        titles = QUOTED.findall(self.text)
        self.text = None
        try:
            people = await find_overlapping_actors(titles, self.bot.tmdb_client)
        except ValueError as err:
            return err.args[0]
        if not people:
            return 'No actors found.'
        return '\n\n'.join(['Results found:'] + [
            ' - {0.name} [{0.url}]'.format(person) for person in people
        ])


class MovieOverlapQueryHandler(BotMessageHandler):
    """Handles queries about actors in the same group of movies.

      If you send me a message asking 'movies with' with a quoted list
      of actors I will find movies featuring all of those actors.

    """

    PHRASE = 'movies with'

    async def __anext__(self):
        if not self.text:
            raise StopAsyncIteration
        names = QUOTED.findall(self.text)
        self.text = None
        try:
            movies = await find_overlapping_movies(names, self.bot.tmdb_client)
        except ValueError as err:
            return err.args[0]
        if not movies:
            return 'No movies found.'
        return '\n\n'.join(['Results found:'] + [
            ' - {0.title} [{0.url}]'.format(movie) for movie in movies
        ])


class MovieQueryHandler(BotMessageHandler):
    """Handles queries about specific movies.

      If you send me a message starting with the word 'movie' I will
      tell you about that movie.

    """

    PHRASE = 'movie'

    async def __anext__(self):
        if self.text is None:
            raise StopAsyncIteration
        title = self.text.split(' ', maxsplit=2)[-1]
        self.text = None
        movie = await self.bot.tmdb_client.find_movie(title)
        return str(movie)


class PersonQueryHandler(BotMessageHandler):
    """Handles queries about specific people.

      If you send me a message starting with the word 'person' I will
      tell you about that person.

    """

    PHRASE = 'person'

    async def __anext__(self):
        if self.text is None:
            raise StopAsyncIteration
        name = self.text.split(' ', maxsplit=2)[-1]
        self.text = None
        person = await self.bot.tmdb_client.find_person(name)
        return str(person)


class Halliwell(SlackBot):
    """The filmgoer's companion.

    Arguments:
      id_ (:py:class:`str`): The BOT's Slack ID.
      user (:py:class:`str`): The BOT's friendly name.
      api (:py:class:`~.SlackApi`): The Slack API wrapper.
      tmdb_client (:py:class:`atmdb.client.TMDbClient`): The TMDb client.

    """

    INSTRUCTIONS = dedent("""
    Halliwell: The filmgoer's companion.

    An aSlack and aTMDb BOT running on Cloud Foundry.

    For more information, see https://github.com/textbook/aslack.
    """)

    MESSAGE_FILTERS = [
        ActorOverlapQueryHandler,
        MovieOverlapQueryHandler,
        MovieQueryHandler,
        PersonQueryHandler,
    ]

    VERSION = 'Halliwell v0.1.0'

    def __init__(self, id_, user, api, tmdb_client=None):
        super().__init__(id_, user, api)
        if tmdb_client is None:
            tmdb_client = TMDbClient.from_env()
        self.tmdb_client = tmdb_client


if __name__ == '__main__':
    # pylint: disable=wrong-import-position,wrong-import-order
    import logging
    import sys

    logging.basicConfig(
        datefmt='%Y/%m/%d %H.%M.%S',
        format='%(levelname)s:%(name)s:%(message)s',
        level=logging.INFO,
        stream=sys.stdout,
    )

    LOOP = asyncio.get_event_loop()
    BOT = LOOP.run_until_complete(Halliwell.from_api_token())
    LOOP.run_until_complete(BOT.join_rtm())
