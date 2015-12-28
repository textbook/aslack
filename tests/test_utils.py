from unittest import mock

from aiohttp.web_exceptions import HTTPForbidden, HTTPMovedPermanently, HTTPOk
import pytest

from aslack.utils import (
    API_TOKEN_ENV,
    get_api_token,
    FriendlyError,
    raise_for_status,
)


@mock.patch('aslack.utils.os')
@mock.patch('aslack.utils.input')
def test_get_api_token_from_input(input, os):
    os.environ = {}
    os.getenv.return_value = None
    test_token = 'token'
    input.return_value = test_token
    assert get_api_token() == test_token
    os.getenv.assert_called_once_with(API_TOKEN_ENV)
    assert input.call_count == 1
    assert os.environ == {API_TOKEN_ENV: test_token}


@mock.patch('aslack.utils.os')
def test_get_api_token_from_environment(os):
    test_token = 'token'
    os.getenv.return_value = test_token
    assert get_api_token() == test_token
    os.getenv.assert_called_once_with(API_TOKEN_ENV)


@pytest.mark.parametrize('input_,expected', [
    (('foo',), ('bar',)),
    (('baz',), ('baz',)),
])
@mock.patch(
    'aslack.utils.FriendlyError.EXPECTED_ERRORS',
    new_callable=mock.PropertyMock,
    return_value={'foo': 'bar'}
)
def test_friendly_error(errors, input_, expected):
    err = FriendlyError(*input_)
    assert isinstance(err, Exception)
    assert err.args == expected


@pytest.mark.parametrize('status,raises', [
    (200, HTTPOk),
    (301, HTTPMovedPermanently),
    (403, HTTPForbidden),
    (1000, None),
])
def test_raise_for_status(status, raises):
    response = mock.MagicMock(status=status)
    if raises is None:
        assert raise_for_status(response) is None
    else:
        with pytest.raises(raises):
            raise_for_status(response)
