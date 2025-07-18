import functools
import concurrent.futures as cf
from typing import Literal
import threading
import sys

# import multiprocessing as mp
# import multiprocess as mps
from ._func_util import debug_enter_exit
from ._errors import UnsupportedExecutor

import logging

logger = logging.getLogger(__name__)

# just to be safe
_get_executor_lock = threading.Lock()


@functools.lru_cache(maxsize=1)
def _get_thread_pool_executor() -> cf.Executor:
    with debug_enter_exit(
        logger, "Creating ThreadPoolExecutor", "Created ThreadPoolExecutor"
    ):
        return cf.ThreadPoolExecutor(thread_name_prefix="streamlit-concurrency")


@functools.lru_cache(maxsize=1)
def _get_process_pool_executor() -> cf.Executor:
    args = {}

    if sys.version_info >= (3, 11):
        # retire executor earlier to be safe
        args["max_tasks_per_child"] = 4

    return cf.ProcessPoolExecutor(
        **args,
        # mp_context=mp.get_context("spawn")
    )


@functools.lru_cache(maxsize=1)
def _get_interpreter_pool_executor() -> cf.Executor:
    # should be available since py3.14
    try:
        return cf.InterpreterPoolExecutor()  # type: ignore
    except AttributeError as e:
        raise NotImplementedError(
            "InterpreterPoolExecutor is not available in this Python version."
            "Please use a different executor type."
        ) from e


@functools.lru_cache(maxsize=1)
def _get_multiprocess_executor() -> cf.Executor:
    raise NotImplementedError


def get_executor(
    executor_type: Literal["thread", "process", "interpreter"],
) -> cf.Executor:
    """Get the executor based on the type."""
    with _get_executor_lock:
        if executor_type == "thread":
            return _get_thread_pool_executor()
        elif executor_type == "process":
            return _get_process_pool_executor()
        elif executor_type == "interpreter":
            return _get_interpreter_pool_executor()
        else:
            raise UnsupportedExecutor(f"Unknown executor type: {executor_type}")
