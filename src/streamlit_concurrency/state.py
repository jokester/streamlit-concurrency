import streamlit
from typing import (
    Callable,
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Any,
    Dict,
    Union,
    overload,
)
from typing_extensions import ParamSpec
from typing_extensions import Self
from ._streamlit_util import assert_st_script_run_ctx
import logging

logger = logging.getLogger(__name__)

S = TypeVar("S")  # State type
A = ParamSpec("A")  # Action type


class Reducer(Protocol, Generic[S, A]):
    def __call__(self, prev: S, *action: A.args, **kwargs: A.kwargs) -> S: ...


class StateRef(Generic[S]):
    """
    A reference to access a slot in dict-like state storage. The storage is in st.session_state.

    Methods are accessilble from all threads but not thread safe. Caller is expected to coordinate for stronger guarantees.
    """

    def __init__(
        self,
        storage: Dict[tuple, Any],
        key: str,
        namespace: Optional[str] = None,
        factory: Union[Callable[[], S], None] = None,
    ):
        self.__storage = storage
        self.__key = key
        self.__namespace = namespace
        if factory is not None:
            self.init(factory)

    def init(self, factory: Callable[[], S]) -> bool:
        """T

        Args:
            factory (Callable[[], S]): called when the state is uninitialized

        Returns:
            bool: the state was uninitialized
        """
        if self.__full_key not in self.__storage:
            self.__storage[self.__full_key] = factory()
            return True
        return False

    @property
    def value(self) -> S:
        try:
            return self.__storage[self.__full_key]
        except KeyError:
            raise KeyError(
                f"StateRef(key={self.__key}, namespace={self.__namespace}) not initialized"
            )

    @value.setter
    def value(self, new_value: S):
        self.__storage[self.__full_key] = new_value
        return self

    # not defining a deleter: deleting a ref (variable & pointer) should not affect the actual value
    # @value.deleter
    # def value(self): self.clear()

    def reduce(self, reducer: Reducer[S, A], *action: A.args, **kwargs: A.kwargs) -> S:
        self.value = reducer(self.value, *action, **kwargs)
        return self.value

    def deinit(self):
        if self.__full_key in self.__storage:
            del self.__storage[self.__full_key]

    @property
    def __full_key(self) -> tuple:
        return (self.__namespace, self.__key)


@overload  # to infer S from type_
def use_state(
    key: str, *, namespace: Optional[str] = None, type_: Type[S], **kwargs: Any
) -> StateRef[S]: ...


@overload  # to infer S from a factory callable
def use_state(
    key: str,
    *,
    namespace: Optional[str] = None,
    factory: Optional[Callable[[], S]] = None,
    **kwargs: Any,
) -> StateRef[S]: ...


@overload  # fallback to infer to Any
def use_state(
    key: str, *, namespace: Optional[str] = None, **kwargs: Any
) -> StateRef[Any]: ...


def use_state(
    key: str,
    *,
    namespace: Optional[str] = None,
    **kwargs: Any,
) -> StateRef[S]:  # type: ignore
    assert_st_script_run_ctx("use_state()")
    storage = streamlit.session_state.get("_streamlit_concurrency_states")
    if storage is None:
        logger.debug(f"initializing state storage for Streamlit session")
        storage = {}
        streamlit.session_state["_streamlit_concurrency_states"] = storage
    full_key = f"{namespace}:|:{key}"
    factory = kwargs.pop("factory", None)
    return StateRef(storage=storage, key=full_key, factory=factory)
