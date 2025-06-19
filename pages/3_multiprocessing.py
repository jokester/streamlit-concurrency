import os
import asyncio
import streamlit as st
from streamlit_concurrency.demo import (
    example_func,
    render_page_src,
    render_repo_file,
    to_github_url,
)
from streamlit_concurrency import run_in_executor
import trio

st.markdown(f"""
A function with `executor='process'` runs in a separate process. This is most helpful for CPU-intensive tasks that can run faster without Python GIL.

There are certain limits to what can be run in a process executor. See [API doc]({to_github_url("API.md")}) for details.
""")
st.write(f"Current Streamlit process pid: {os.getpid()}")

dest = st.empty()

#
transformed_sync = run_in_executor(executor="process", cache={"ttl": 5})(
    example_func.cpu_intensive_computation
)


# don't do this: a function must be "importable" to be used with a process executor
# @run_in_executor(executor="process", cache={"ttl": 5})
# def foo(): ...


run_clicked = st.button("Run 2 CPU-intensive tasks in process executor")

render_page_src(__file__)

render_repo_file(
    "src/streamlit_concurrency/demo/example_func.py",
    "streamlit_concurrency.demo.example_func",
)


async def main():
    dest.markdown(f"""
res1: running...

res2: running...
""")
    (res1, pid1), (res2, pid2), (res3, pid3) = await asyncio.gather(
        transformed_sync(100),
        transformed_sync(200000000),
        # example_func.cpu_intensive_computation_in_process_executor(2000),
        trio.run_process(
            example_func.cpu_intensive_computation_in_process_executor, 2000
        ),
    )
    dest.markdown(f"""
res1: {res1} computed in process {pid1}

res2: {res2} computed in process {pid2}
""")


if run_clicked:
    asyncio.run(main())
