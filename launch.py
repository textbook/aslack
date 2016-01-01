import asyncio
import logging
import sys

from examples.halliwell import Halliwell

logging.basicConfig(
    datefmt='%Y/%m/%d %H.%M.%S',
    format='%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO,
    stream=sys.stdout,
)


loop = asyncio.get_event_loop()

bot = loop.run_until_complete(Halliwell.from_api_token())

loop.run_until_complete(bot.join_rtm())
