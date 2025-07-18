import asyncio
import concurrent.futures as cf
import streamlit as st
import functools
import contextlib
import logging

from typing import (
    Coroutine,
    Union,
    TypeVar,
    Callable,
)
from typing_extensions import ParamSpec
from ._func_util import (
    assert_is_transformable_sync,
    debug_enter_exit,
    assert_is_importable_func,
)
from ._streamlit_util import (
    assert_st_script_run_ctx,
    create_script_run_context_cm,
)
from ._executors import get_executor
from ._func_cache import CacheConf

R = TypeVar("R")
P = ParamSpec("P")

logger = logging.getLogger(__name__)


def transform_sync(
    func: Callable[P, R],
    *,
    executor: cf.Executor,
    cache: Union[CacheConf, dict, None] = None,
    with_script_run_context: bool = False,
) -> Callable[P, Coroutine[None, None, R]]:
    """Transforms a *sync* function to do real work in executor

    @param cache: configuration to pass to st.cache_data()

    @param executor: executor to run the function in

    @param with_script_run_context: if True, the thread running provided function will be run with a ScriptRunContext.

    See [multithreading](https://docs.streamlit.io/develop/concepts/design/multithreading) for possible motivation and consequences.
    This option must be used with a ThreadPoolExecutor.

    @return: an async function

    """
    assert_is_transformable_sync(func)

    assert isinstance(executor, cf.Executor)

    if with_script_run_context and not isinstance(executor, cf.ThreadPoolExecutor):
        raise ValueError(
            "with_script_run_context=True can only be used with a ThreadPoolExecutor"
        )

    if not isinstance(executor, cf.ThreadPoolExecutor):
        assert_is_importable_func(func)
        assert not with_script_run_context
        dispatch_and_wait = _transform_for_remote_executor(func, executor)
        return transform_sync(
            dispatch_and_wait, executor=get_executor("thread"), cache=cache
        )

    # dump_func_metadata(func)
    # dump_func_code("wrap_sync", func)

    async def wrapper(*args_, **kwargs_) -> R:
        # a wrapper that
        # 1. capture possible ScriptRunContext
        # 2. run decorated `func` in executor, with the ScriptRunContext context-managed
        # 3. return a Awaitable
        if with_script_run_context:
            cm = create_script_run_context_cm(
                assert_st_script_run_ctx(f"<@run_in_executor(...) def {func.__name__}>")
            )
        else:
            cm = contextlib.nullcontext()

        # the sync function to run in executor, doing the real work
        def run_in_executor(*args, **kwargs) -> R:
            # NOTE: need to make sure this works with other executors
            if cache is None:
                with debug_enter_exit(
                    logger,
                    f"executing original {func.__name__}",
                    f"executed original {func.__name__}",
                ):
                    with cm:
                        return func(*args, **kwargs)
            # else: wrap with st.cache_data first

            # NOTE st.cache_data needs the provided user function
            # internally it creates cache key for the function from __module__ __qualname__ __code__ etc

            # NOTE cm is not required to call st.cache_data when show_spinner=False
            func_with_cache = st.cache_data(func, **{**cache, "show_spinner": False})
            with debug_enter_exit(
                logger,
                f"executing cached {func.__name__}",
                f"executed cached {func.__name__}",
            ):
                with cm:
                    return func_with_cache(*args, **kwargs)

        future = executor.submit(run_in_executor, *args_, **kwargs_)
        return await asyncio.wrap_future(future)

    return functools.update_wrapper(wrapper, func)


def _transform_for_remote_executor(func: Callable, executor: cf.Executor) -> Callable:
    """
    Returns:
        Callable: a wrapper that works with st.cache_data()
    """

    def wrapper(*args, **kwargs):
        return executor.submit(func, *args, **kwargs).result()

    # allow st.cache_* API to distinguish inner functions
    wrapper.__qualname__ = func.__qualname__

    return wrapper
