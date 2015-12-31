import json

import aiohttp
from asynctest import mock
import pytest

from aslack.slack_api import SlackApiError, SlackBotApi
from aslack.slack_bot import SlackBot
from helpers import AsyncContextManager, AsyncIterable


@mock.patch('aslack.slack_bot.randint', return_value=10)
def test_init(randint):
    args = dict(id_='foo', user='bar', api='baz')
    bot = SlackBot(**args)
    for attr, val in args.items():
        assert getattr(bot, attr) == val
    assert bot.address_as == '<@foo>: '
    assert bot.full_name == '<@foo>'
    assert next(bot._msg_ids) == randint.return_value
    randint.assert_called_once_with(1, 1000)


@mock.patch(
    'aslack.slack_bot.SlackBotApi.execute_method',
    return_value={'user_id': 'foo', 'user': 'bar'},
)
@pytest.mark.asyncio
async def test_from_api_token(execute_method):
    dummy_token = 'token'
    bot = await SlackBot.from_api_token(dummy_token)
    execute_method.assert_called_once_with('auth.test')
    assert bot.id_ == 'foo'
    assert bot.user == 'bar'


@pytest.mark.asyncio
async def test_get_socket_url():
    api = mock.CoroutineMock(
        spec=SlackBotApi,
        **{'execute_method.return_value': {'url': 'foo'}},
    )
    bot = SlackBot(None, None, api)
    url = await bot.get_socket_url()
    assert url == 'foo'
    api.execute_method.assert_called_once_with(
        'rtm.start',
        simple_latest=True,
        no_unreads=True,
    )


def test_unpack_message_success():
    data = {'bar': 'foo'}
    mock_message = mock.Mock(data=json.dumps(data))
    assert SlackBot._unpack_message(mock_message) == data


def test_unpack_message_no_data():
    with pytest.raises(AttributeError):
        SlackBot._unpack_message(object())


def test_unpack_message_broken_json():
    mock_message = mock.Mock(data='broken.json')
    with pytest.raises(json.JSONDecodeError):
        SlackBot._unpack_message(mock_message)


@pytest.mark.parametrize('data,raises', [
    ('{"type": "hello"}', None),
    ('{"foo": "bar"}', SlackApiError),
    ('broken.json', json.JSONDecodeError),
])
def test_validate_first_message(data, raises):
    mock_message = mock.Mock(data=data)
    if raises is None:
        assert SlackBot._validate_first_message(mock_message) is None
    else:
        with pytest.raises(raises):
            SlackBot._validate_first_message(mock_message)


@mock.patch('aslack.slack_bot.randint', return_value=10)
def test_format_message(randint):
    bot = SlackBot(None, None, None)
    expected = dict(
        id=randint.return_value,
        channel='foo',
        text='bar',
        type='message',
    )
    assert json.loads(bot._format_message('foo', 'bar')) == expected


@mock.patch('aslack.slack_bot.randint', return_value=10)
def test_handle_message_dispatch(randint):
    bot = SlackBot(None, None, None)
    mock_message = mock.Mock(data='{}')
    mock_filter_ = mock.Mock(return_value=True)
    mock_dispatch = mock.Mock(return_value=dict(channel='foo', text='bar'))
    response = bot.handle_message(mock_message, {mock_filter_: mock_dispatch})
    expected = dict(
        id=randint.return_value,
        type='message',
        **mock_dispatch.return_value,
    )
    assert json.loads(response) == expected
    mock_filter_.assert_called_once_with({})
    mock_dispatch.assert_called_once_with({})


@mock.patch('aslack.slack_bot.randint', return_value=10)
def test_handle_help_message(randint):
    bot = SlackBot('foo', None, None)
    mock_msg = mock.Mock(
        data=json.dumps(dict(channel='bar', text='<@foo>: ?', type='message')),
    )
    expected = dict(
        channel='bar',
        id=randint.return_value,
        text=bot._instruction_list({}),
        type='message',
    )
    response = bot.handle_message(mock_msg, {})
    assert json.loads(response) == expected

def test_handle_error_message():
    bot = SlackBot(None, None, None)
    mock_msg = mock.Mock(data=json.dumps(dict(error={}, type='error')))
    with pytest.raises(SlackApiError):
        bot.handle_message(mock_msg, {})


def test_handle_unfiltered_message():
    bot = SlackBot(None, None, None)
    mock_msg = mock.Mock(data=json.dumps(dict(type='message')))
    bot.handle_message(mock_msg, {lambda msg: False: None})


@pytest.mark.parametrize('input_,output', [
    ({'type': 'message', 'text': '<@foo>: something'}, True),
    ({'type': 'message', 'text': 'something <@foo>: else'}, False),
    ({'type': 'message', 'text': 'something else'}, False),
])
def test_to_me(input_, output):
    bot = SlackBot('foo', None, None)
    assert bot.message_is_to_me(input_) == output


@pytest.mark.parametrize('input_,output', [
    ({'type': 'message', 'text': '<@foo>: something'}, True),
    ({'type': 'message', 'text': 'something <@foo>: else'}, True),
    ({'type': 'message', 'text': 'something else'}, False),
])
def test_mentions_me(input_, output):
    bot = SlackBot('foo', None, None)
    assert bot.message_mentions_me(input_) == output


def test_instruction_list():
    bot = SlackBot('foo', None, None)
    def filter_():
        """foo"""
    def dispatch():
        """bar"""
    instructions = bot._instruction_list({filter_: dispatch})
    assert instructions.endswith('foo bar')
    assert instructions.startswith(SlackBot.INSTRUCTIONS.strip())
    assert '"&lt;@foo&gt;: ?"' in instructions


@mock.patch('aslack.slack_bot.ws_connect')
@pytest.mark.asyncio
async def test_join_rtm_simple(ws_connect):
    ws_connect.return_value = AsyncContextManager(
        AsyncIterable.from_test_data(
            receive=mock.Mock(data='{"type": "hello"}'),
        )
    )
    api = mock.CoroutineMock(
        spec=SlackBotApi,
        **{'execute_method.return_value': {'url': 'foo'}},
    )
    bot = SlackBot(None, None, api)
    await bot.join_rtm()
    api.execute_method.assert_called_once_with(
        'rtm.start',
        simple_latest=True,
        no_unreads=True,
    )


@pytest.mark.parametrize('closed,calls', [
    (True, 0),
    (False, 1),
])
@mock.patch('aslack.slack_bot.ws_connect')
@pytest.mark.asyncio
async def test_join_rtm_error_messages(ws_connect, closed, calls):
    mock_msg = mock.Mock(tp=aiohttp.MsgType.closed)
    mock_socket = AsyncIterable.from_test_data(
        mock_msg,
        close=None,
        receive=mock.Mock(data='{"type": "hello"}'),
    )
    mock_socket.closed = closed
    ws_connect.return_value = AsyncContextManager(mock_socket)
    api = mock.CoroutineMock(
        spec=SlackBotApi,
        **{'execute_method.return_value': {'url': 'foo'}},
    )
    bot = SlackBot(None, None, api)
    await bot.join_rtm()
    api.execute_method.assert_called_once_with(
        'rtm.start',
        simple_latest=True,
        no_unreads=True,
    )
    assert mock_socket.close.call_count == calls


@mock.patch('aslack.slack_bot.ws_connect')
@pytest.mark.asyncio
async def test_join_rtm_messages(ws_connect):
    mock_msg = mock.Mock(tp=aiohttp.MsgType.text, data='{"type": "hello"}')
    mock_socket = AsyncIterable.from_test_data(
        mock_msg,
        close=None,
        receive=mock.Mock(data='{"type": "hello"}'),
        send_str=None,
    )
    ws_connect.return_value = AsyncContextManager(mock_socket)
    api = mock.CoroutineMock(
        spec=SlackBotApi,
        **{'execute_method.return_value': {'url': 'foo'}},
    )
    bot = SlackBot(None, None, api)
    await bot.join_rtm({
        lambda msg: True: lambda msg: {'channel': 'foo', 'text': 'bar'},
    })
    api.execute_method.assert_called_once_with(
        'rtm.start',
        simple_latest=True,
        no_unreads=True,
    )
    assert mock_socket.send_str.call_count == 1
