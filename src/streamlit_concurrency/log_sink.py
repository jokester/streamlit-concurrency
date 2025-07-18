"""
Log sink to capture log records and formatted log lines as a context manager.

Currently only used for test and demo.
"""

import logging
import contextlib
from typing import Iterable, Optional, Union
import streamlit.logger as st_logger

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def create_log_sink(
    level: int = logging.INFO,
    logger_names: Optional[Iterable[str]] = None,
    format: Union[
        str, None
    ] = "%(asctime)s %(levelname)s %(threadName)s %(name)s - %(funcName)s: %(message)s",
    capture_streamlit_log: bool = False,
):
    """Attach a log sink to Python root logger or stream to capture LogRecord-s and formatted log lines"""
    records: list[logging.LogRecord] = []
    lines: list[str] = []

    if logger_names is not None:
        logger_names = frozenset(logger_names)

    formatter = format and logging.Formatter(format)

    handler = logging.NullHandler(level)

    def append_log(record: logging.LogRecord) -> bool:
        if logger_names is None or record.name in logger_names:
            records.append(record)

            if formatter:
                lines.append(formatter.format(record))
            return True
        return False

    handler.handle = append_log

    log_src = st_logger.get_logger("root") if capture_streamlit_log else logging.root

    log_src.addHandler(handler)

    yield records, lines

    log_src.removeHandler(handler)
    handler.close()
