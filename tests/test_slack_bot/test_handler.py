from asynctest import mock
import pytest

from aslack.slack_bot import BotMessageHandler, MessageHandler, SlackBot


@pytest.mark.asyncio
async def test_async_for():
    async for _ in MessageHandler():
        pass


@pytest.mark.asyncio
async def test_bot_handler_dispatch():
    dummy_message = 'I am the bot'
    dummy_bot = object()
    handler = BotMessageHandler(dummy_bot)
    with mock.patch.object(BotMessageHandler, '__anext__') as _next:
        _next.side_effect = [dummy_message, StopAsyncIteration]
        async for message in handler:
            assert message == dummy_message
    assert handler.bot is dummy_bot


def test_bot_handler_matching():
    bot = SlackBot('foo', None, None)
    handler = BotMessageHandler(bot)
    handler.PHRASE = 'bar'
    text = '<@foo>: bar'
    assert handler.matches(dict(type='message', text=text))
    assert handler.text == text


def test_handler_description():
    description = MessageHandler().description()
    assert description.startswith('Arguments')
    assert description.endswith('each message.')
