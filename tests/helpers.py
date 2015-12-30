from asynctest import mock


class EmptyAsyncIterable:

    async def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class AsyncIterable(EmptyAsyncIterable):

    def __init__(self, iters):
        self.iters = iter(iters)

    async def __anext__(self):
        try:
            return next(self.iters)
        except StopIteration:
            raise StopAsyncIteration


def async_context_manager_factory(aenter):
    class AsyncContextManager:
        async def __aenter__(self):
            return aenter
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    return AsyncContextManager()


def async_iterable_factory(*iters, **methods):
    if iters:
        inst = AsyncIterable(iters)
    else:
        inst = EmptyAsyncIterable()
    for name, return_value in methods.items():
        setattr(inst, name, mock.CoroutineMock(return_value=return_value))
    return inst
