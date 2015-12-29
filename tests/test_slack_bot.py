import json

from asynctest import mock
import pytest

from aslack.slack_api import SlackApiError, SlackBotApi
from aslack.slack_bot import SlackBot


def test_init():
    args = dict(id_='foo', user='bar', api='baz')
    bot = SlackBot(**args)
    for attr, val in args.items():
        assert getattr(bot, attr) == val


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
    url = await bot._get_socket_url()
    assert url == 'foo'
    api.execute_method.assert_called_once_with('rtm.start')


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
@mock.patch('aslack.slack_bot.logging')
def test_validate_first_message(logging, data, raises):
    mock_message = mock.Mock(data=data)
    if raises is None:
        assert SlackBot._validate_first_message(mock_message) is None
    else:
        with pytest.raises(raises):
            SlackBot._validate_first_message(mock_message)
