import asyncio
import logging
from textwrap import dedent
import sys

from aslack import __author__, slack_bot

logging.basicConfig(
    datefmt='%Y/%m/%d %H.%M.%S',
    format='%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO,
    stream=sys.stdout,
)


class Halliwell(slack_bot.SlackBot):
    """Trivial bot with slightly more useful instructions."""

    INSTRUCTIONS = dedent("""
    Hello, I am an aSlack bot running on Cloud Foundry.

    For more information, see {aslack_url} or contact {author}.
    """.format(
        aslack_url='https://pythonhosted.org/aslack',
        author=__author__,
    ))


loop = asyncio.get_event_loop()

bot = loop.run_until_complete(Halliwell.from_api_token())

loop.run_until_complete(bot.join_rtm())
