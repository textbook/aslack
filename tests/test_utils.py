from unittest import mock

from aiohttp.web_exceptions import HTTPForbidden, HTTPMovedPermanently, HTTPOk
import pytest

from aslack.utils import (
    FriendlyError,
    raise_for_status,
    truncate,
)


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


@pytest.mark.parametrize('args,kwargs,output', [
    (('',), {}, ''),
    (('foo bar baz',), {}, 'foo bar baz'),
    (('foo bar baz',), {'max_len': 10}, 'foo bar...'),
    (('foo bar baz',), {'end': ' - ', 'max_len': 10}, 'foo bar - '),
])
def test_truncate(args, kwargs, output):
    assert truncate(*args, **kwargs) == output
