import asyncio

from aiohttp.web_exceptions import HTTPException
from asynctest import mock
import pytest

from aslack.slack_api import SlackApi, SlackApiError

DUMMY_TOKEN = 'token'


@mock.patch('aslack.slack_api.aiohttp')
async def test_execute_method_success(aiohttp):
    result = {'ok': True}
    json_future = asyncio.Future()
    json_future.set_result(result)
    resp_future = asyncio.Future()
    resp_future.set_result(
        mock.MagicMock(status=200, **{'json.return_value': json_future})
    )
    aiohttp.get.return_value = resp_future
    api = SlackApi(DUMMY_TOKEN)
    method = 'auth.test'
    response = await api.execute_method(method)
    assert response == result
    aiohttp.get.assert_called_once_with(
        SlackApi._create_url(method),
        params={'token': DUMMY_TOKEN},
    )


@mock.patch('aslack.slack_api.aiohttp')
async def test_execute_method_api_failure(aiohttp):
    result = {'ok': False, 'error': 'foo'}
    json_future = asyncio.Future()
    json_future.set_result(result)
    resp_future = asyncio.Future()
    resp_future.set_result(
        mock.MagicMock(status=200, **{'json.return_value': json_future})
    )
    aiohttp.get.return_value = resp_future
    api = SlackApi(DUMMY_TOKEN)
    method = 'auth.test'
    with pytest.raises(SlackApiError):
        await api.execute_method(method)
    aiohttp.get.assert_called_once_with(
        SlackApi._create_url(method),
        params={'token': DUMMY_TOKEN},
    )


@mock.patch('aslack.slack_api.aiohttp')
async def test_execute_method_http_failure(aiohttp):
    future = asyncio.Future()
    future.set_result(
        mock.MagicMock(status=500, message='failed')
    )
    aiohttp.get.return_value = future
    api = SlackApi(DUMMY_TOKEN)
    method = 'auth.test'
    with pytest.raises(HTTPException):
        await api.execute_method(method)
    aiohttp.get.assert_called_once_with(
        'https://slack.com/api/auth.test',
        params={'token': DUMMY_TOKEN},
    )


@pytest.mark.parametrize('args,need_token', [
    [(), True],
    [(DUMMY_TOKEN,), False],
])
@mock.patch('aslack.slack_api.get_api_token')
def test_init(get_api_token, args, need_token):
    get_api_token.return_value = DUMMY_TOKEN
    api = SlackApi(*args)
    assert api.token == DUMMY_TOKEN
    if need_token:
        get_api_token.assert_called_once_with()


@pytest.mark.parametrize('method,exists', [
    ('auth.test', True),
    ('foo.bar', False)
])
def test_create_url(method, exists):
    if exists:
        expected = 'https://slack.com/api/{}'.format(method)
        assert SlackApi._create_url(method) == expected
    else:
        with pytest.raises(SlackApiError):
            SlackApi._create_url(method)
