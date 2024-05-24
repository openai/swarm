# Copyright 2016 Étienne Bersac
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import sys
import typing as t

from tenacity import AttemptManager
from tenacity import BaseRetrying
from tenacity import DoAttempt
from tenacity import DoSleep
from tenacity import RetryCallState
from tenacity import _utils

WrappedFnReturnT = t.TypeVar("WrappedFnReturnT")
WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Awaitable[t.Any]])


def asyncio_sleep(duration: float) -> t.Awaitable[None]:
    # Lazy import asyncio as it's expensive (responsible for 25-50% of total import overhead).
    import asyncio

    return asyncio.sleep(duration)


class AsyncRetrying(BaseRetrying):
    sleep: t.Callable[[float], t.Awaitable[t.Any]]

    def __init__(
        self,
        sleep: t.Callable[[float], t.Awaitable[t.Any]] = asyncio_sleep,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep

    async def __call__(  # type: ignore[override]
        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        while True:
            do = await self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                try:
                    result = await fn(*args, **kwargs)
                except BaseException:  # noqa: B902
                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
                else:
                    retry_state.set_result(result)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                await self.sleep(do)
            else:
                return do  # type: ignore[no-any-return]

    @classmethod
    def _wrap_action_func(cls, fn: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        if _utils.is_coroutine_callable(fn):
            return fn

        async def inner(*args: t.Any, **kwargs: t.Any) -> t.Any:
            return fn(*args, **kwargs)

        return inner

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(self._wrap_action_func(fn))

    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.iter_state.retry_run_result = await self._wrap_action_func(self.retry)(
            retry_state
        )

    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        if self.wait:
            sleep = await self._wrap_action_func(self.wait)(retry_state)
        else:
            sleep = 0.0

        retry_state.upcoming_sleep = sleep

    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = await self._wrap_action_func(self.stop)(
            retry_state
        )

    async def iter(
        self, retry_state: "RetryCallState"
    ) -> t.Union[DoAttempt, DoSleep, t.Any]:  # noqa: A003
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = await action(retry_state)
        return result

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        raise TypeError("AsyncRetrying object is not iterable")

    def __aiter__(self) -> "AsyncRetrying":
        self.begin()
        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
        return self

    async def __anext__(self) -> AttemptManager:
        while True:
            do = await self.iter(retry_state=self._retry_state)
            if do is None:
                raise StopAsyncIteration
            elif isinstance(do, DoAttempt):
                return AttemptManager(retry_state=self._retry_state)
            elif isinstance(do, DoSleep):
                self._retry_state.prepare_for_next_attempt()
                await self.sleep(do)
            else:
                raise StopAsyncIteration

    def wraps(self, fn: WrappedFn) -> WrappedFn:
        fn = super().wraps(fn)
        # Ensure wrapper is recognized as a coroutine function.

        @functools.wraps(
            fn, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        async def async_wrapped(*args: t.Any, **kwargs: t.Any) -> t.Any:
            return await fn(*args, **kwargs)

        # Preserve attributes
        async_wrapped.retry = fn.retry  # type: ignore[attr-defined]
        async_wrapped.retry_with = fn.retry_with  # type: ignore[attr-defined]

        return async_wrapped  # type: ignore[return-value]
