# streamlit-concurrency

Library for easier and safer concurrency for streamlit.

This library provide 2 APIs:

- `run_in_executor`: transform function to run concurrently in executor (ThreadPoolExecutor)
    - with configurable caching like `st.cache_data`, even for async function
    - transformed function can access `st.session_state` and widgets from other threads
- `use_state`: manage page state in and across pages

Links:

- [Demo](https://concurrency.streamlit.app/)
- [API](https://github.com/jokester/streamlit-concurrency/blob/main/API.md)
- [Github](https://github.com/jokester/streamlit-concurrency/)
- [pypi](https://pypi.org/project/streamlit-concurrency/)


## License

Apache 2.0