import asyncio
import concurrent.futures as cf
import streamlit as st
import functools
import contextlib
import logging

from typing import Coroutine, Optional, TypeVar, Callable, Union
from typing_extensions import ParamSpec

from ._errors import UnsupportedExecutor
from ._func_util import (
    assert_is_transformable_async,
    debug_enter_exit,
)
from ._streamlit_util import (
    assert_st_script_run_ctx,
    create_script_run_context_cm,
)
from ._func_cache import CacheConf
from ._executors import get_executor

R = TypeVar("R")
P = ParamSpec("P")
logger = logging.getLogger(__name__)


def transform_async(
    func: Callable[P, Coroutine[None, None, R]],
    *,
    executor: cf.Executor,
    cache: Union[CacheConf, dict, None] = None,
    with_script_run_context: bool = False,
) -> Callable[P, Coroutine[None, None, R]]:
    """Transforms a *async* function to do real work in executor

    @param cache: configuration to pass to st.cache_data()

    @param executor: executor to run the function in

    @param with_script_run_context: if True, the thread running provided function will be run with a ScriptRunContext.

    See [multithreading](https://docs.streamlit.io/develop/concepts/design/multithreading) for possible motivation and consequences.
    This option must be used with a ThreadPoolExecutor.

    @return: an async function

    """
    assert_is_transformable_async(func)

    if not isinstance(executor, cf.ThreadPoolExecutor):
        raise UnsupportedExecutor(
            f"async function only works with 'thread' executor. Got {executor}"
        )

    async def wrapper(*args, **kwargs) -> R:
        if with_script_run_context:
            cm = create_script_run_context_cm(
                assert_st_script_run_ctx(
                    f"<@run_in_executor(..) async def {func.__name__}>"
                )
            )
        else:
            cm = contextlib.nullcontext()

        # the sync function to run in executor, doing the real work
        def run_in_executor(*args, **kwargs) -> R:
            with cm:
                with debug_enter_exit(
                    logger,
                    f"executing original {func.__name__}",
                    f"executed original {func.__name__}",
                ):
                    # assumes a 'clean' thread without an event loop
                    return asyncio.run(func(*args, **kwargs))

        # simpler case: similar to decorator_sync
        if cache is None:
            with debug_enter_exit(
                logger,
                f"start waiting for {func.__name__}",
                f"finished waiting for {func.__name__}",
            ):
                return await asyncio.wrap_future(
                    executor.submit(run_in_executor, *args, **kwargs)
                )

        # else: create a sync function to use st.cache_data
        waiter_executor = get_executor("thread")

        def wait_in_another_executor(*args, **kwargs) -> R:
            with debug_enter_exit(
                logger,
                f"start waiting for {run_in_executor.__name__} wrapping {func.__name__}",
                f"finish waiting for {run_in_executor.__name__} wrapping {func.__name__}",
            ):
                return waiter_executor.submit(run_in_executor, *args, **kwargs).result()

        # NOTE unlike in the sync case where we can use st.cache_data directly,
        # this hack is required for st.cache to create different cache key for each run_in_executor instance
        # see https://github.com/streamlit/streamlit/issues/11157
        wait_in_another_executor.__qualname__ += f" wrapping {func.__qualname__}"

        wait_in_another_executor = st.cache_data(**{**cache, "show_spinner": False})(
            wait_in_another_executor
        )

        future = waiter_executor.submit(wait_in_another_executor, *args, **kwargs)
        with debug_enter_exit(
            logger,
            f"start waiting for cached {func.__name__}",
            f"finish waiting for cached {func.__name__}",
        ):
            return await asyncio.wrap_future(future)

    return functools.update_wrapper(wrapper, func)
