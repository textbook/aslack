"""Dummy object implementations for testing purposes."""

from asynctest import mock


class AsyncIterable:

    def __init__(self, iters):
        self.iters = iter(iters)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iters)
        except StopIteration:
            raise StopAsyncIteration

    @classmethod
    def from_test_data(cls, *iters, **methods):
        inst = cls(iters)
        for name, return_value in methods.items():
            setattr(inst, name, mock.CoroutineMock(return_value=return_value))
        return inst


class AsyncContextManager:

    def __init__(self, aenter):
        self.aenter = aenter

    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
