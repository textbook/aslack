import asyncio

from aiohttp.web_exceptions import HTTPException
from asynctest import mock
import pytest

from aslack.slack_api import (
    SlackApi, SlackApiError, api_subclass_factory, ALL,
)

DUMMY_TOKEN = 'token'


@pytest.mark.parametrize('status,result,error', [
    (200, {'ok': True}, None),
    (200, {'ok': False, 'error': 'foo'}, SlackApiError),
    (500, {}, HTTPException),
])
@mock.patch('aslack.slack_api.aiohttp')
@pytest.mark.asyncio
async def test_execute_method(aiohttp, status, result, error):
    json_future = asyncio.Future()
    json_future.set_result(result)
    resp_future = asyncio.Future()
    resp_future.set_result(mock.MagicMock(
        status=status,
        message='failed',
        **{'json.return_value': json_future}
    ))
    aiohttp.get.return_value = resp_future
    api = SlackApi(api_token=DUMMY_TOKEN)
    method = 'auth.test'
    if error is None:
        assert await api.execute_method(method) == result
    else:
        with pytest.raises(error):
            await api.execute_method(method)
    aiohttp.get.assert_called_once_with(
        'https://slack.com/api/{}?token={}'.format(method, DUMMY_TOKEN)
    )


@pytest.mark.parametrize('kwargs,need_token', [
    [{}, True],
    [{'api_token': DUMMY_TOKEN}, False],
])
@mock.patch('aslack.core.getenv')
def test_init(getenv, kwargs, need_token):
    getenv.return_value = DUMMY_TOKEN
    if need_token:
        api = SlackApi.from_env()
        getenv.assert_called_once_with(SlackApi.TOKEN_ENV_VAR)
    else:
        api = SlackApi(**kwargs)
    assert api.api_token == DUMMY_TOKEN


def test_api_subclass_factory():
    base_methods = {
        'keep none': {'foo': None, 'bar': None},
        'keep all': {'foo': None, 'bar': None},
        'keep some': {'foo': None, 'bar': None},
    }
    expected = {
        'keep all': {'foo': None, 'bar': None},
        'keep some': {'foo': None},
    }
    docstring = 'test docstring'
    name = 'Child'
    Parent = type(
        'Parent',
        (object,),
        {'FOO': object(), 'API_METHODS': base_methods},
    )
    Child = api_subclass_factory(
        name=name,
        docstring=docstring,
        remove_methods={'keep none': ALL, 'keep some': ('bar',)},
        base=Parent,
    )
    assert Child.FOO is Parent.FOO
    assert Child.__name__ == name
    assert Child.__doc__ == docstring
    assert Child.API_METHODS == expected
