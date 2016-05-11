"""Example aSlack bot to give you information on movies."""
from collections import OrderedDict
import re
from textwrap import dedent

import asyncio

from atmdb import TMDbClient
from atmdb.utils import find_overlapping_actors, find_overlapping_movies

from aslack.slack_bot import SlackBot

QUOTED = re.compile(r'"([^"]+)"')
"""Regular expression to extract quoted text."""


class Halliwell(SlackBot):
    """The filmgoer's companion.

    Arguments:
      id_ (:py:class:`str`): The BOT's Slack ID.
      user (:py:class:`str`): The BOT's friendly name.
      api (:py:class:`SlackApi`): The Slack API wrapper.
      tmdb_client (:py:class:`TMDbClient`): The TMDb client.

    """

    INSTRUCTIONS = dedent("""
    Halliwell: The filmgoer's companion.

    An aSlack and aTMDb BOT running on Cloud Foundry.

    For more information, see https://github.com/textbook/aslack.
    """)

    VERSION = 'Halliwell v0.1.0'

    def __init__(self, id_, user, api, tmdb_client=None):
        super().__init__(id_, user, api)
        if tmdb_client is None:
            tmdb_client = TMDbClient.from_env()
        self.tmdb_client = tmdb_client

    # Matches

    def message_is_movie_query(self, data):
        """If you send me a message starting with the word 'movie'"""
        return (self.message_is_to_me(data) and
                data['text'][len(self.address_as):].startswith('movie'))

    def message_is_person_query(self, data):
        """If you send me a message starting with the word 'person'"""
        return (self.message_is_to_me(data) and
                data['text'][len(self.address_as):].startswith('person'))

    def message_is_actor_multiple_query(self, data):
        """If you send me a message asking 'actors in' with a quoted list of movies"""
        return (self.message_is_to_me(data) and
                data['text'][len(self.address_as):].startswith('actors in'))

    def message_is_movie_multiple_query(self, data):
        """If you send me a message asking 'movies with' with a quoted list of actors"""
        return (self.message_is_to_me(data) and
                data['text'][len(self.address_as):].startswith('movies with'))

    # Dispatchers

    async def provide_movie_data(self, data):
        """I will tell you about that movie."""
        title = data['text'].split(' ', maxsplit=2)[-1]
        movie = await self.tmdb_client.find_movie(title)
        return dict(channel=data['channel'], text=str(movie))

    async def provide_person_data(self, data):
        """I will tell you about that person."""
        name = data['text'].split(' ', maxsplit=2)[-1]
        person = await self.tmdb_client.find_person(name)
        return dict(channel=data['channel'], text=str(person))

    async def find_overlapping_actors(self, data):
        """I will find actors appearing in all of those movies."""
        titles = QUOTED.findall(data['text'])
        try:
            people = await find_overlapping_actors(titles, self.tmdb_client)
        except ValueError as err:
            text = err.args[0]
        else:
            if not people:
                text = 'No actors found.'
            else:
                text = '\n\n'.join(['Results found:'] + [
                    ' - {0.name} [{0.url}]'.format(person) for person in people
                    ])
        return dict(channel=data['channel'], text=text)

    async def find_overlapping_movies(self, data):
        """I will find movies featuring all of those actors."""
        names = QUOTED.findall(data['text'])
        try:
            movies = await find_overlapping_movies(names, self.tmdb_client)
        except ValueError as err:
            text = err.args[0]
        else:
            if not movies:
                text = 'No movies found.'
            else:
                text = '\n\n'.join(['Results found:'] + [
                    ' - {0.title} [{0.url}]'.format(movie) for movie in movies
                ])
        return dict(channel=data['channel'], text=text)

    MESSAGE_FILTERS = OrderedDict([
        (message_is_actor_multiple_query, find_overlapping_actors),
        (message_is_movie_multiple_query, find_overlapping_movies),
        (message_is_movie_query, provide_movie_data),
        (message_is_person_query, provide_person_data),
    ])


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
