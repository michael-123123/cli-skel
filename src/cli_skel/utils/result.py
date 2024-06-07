__all__ = [
    'Ok',
    'Err',
    'Result',
    'ResultBase',
    'get_result',
]


import io
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Optional, IO, NoReturn, Callable, ParamSpec

from cli_skel.utils.context_utils import redirect_outputs

type IOType = IO | io.IOBase | io.StringIO


@dataclass
class ResultBase[_T](ABC):
    """
    An abstract base class for the Result types Ok and Err.
    Shouldn't be used directly.
    """

    @abstractmethod
    def is_ok(self) -> bool:
        pass

    def is_err(self) -> bool:
        return not self.is_ok()

    @abstractmethod
    def getvalue(self, strict: bool = True) -> _T:
        pass

    @abstractmethod
    def setvalue(self, newval: _T, store: Optional[str] = None, strict: bool = True) -> None:
        pass


@dataclass
class Ok[_T](ResultBase[_T]):
    """
    A returned `Ok(...)` object recognizes that some
    computation concluded without any errors.

    The result of the computation (if one exists)
    can be found in `Ok.value`, and should be retrieved
    with `Ok.getvalue()`.
    """

    value: _T
    metadata: dict = field(default_factory=dict)

    def is_ok(self) -> bool:
        return True

    def getvalue(self, strict: bool = True):
        return self.value

    def setvalue(self, newval: _T, store: Optional[str] = None, strict: bool = True) -> None:
        if store is not None:
            self.metadata[store] = self.value
        self.value = newval

    def __getattr__(self, key: str) -> Any:
        try:
            return self.metadata[key]
        except (TypeError, KeyError):
            raise AttributeError(key) from None


@dataclass
class Err[_T](ResultBase[_T]):
    """
    A returned `Err(...)` object indicates that some
    computation encountered an error, and did not conclude successfully.

    The underlying error (if one exists)
    can be found in `Err.error`, and should be retrieved
    with `Err.asexception`.
    """

    error: Optional[BaseException] = None
    stdout: Optional[IOType] = None
    stderr: Optional[IOType] = None
    default: Optional[Any] = None
    metadata: dict = field(default_factory=dict)

    def is_ok(self) -> bool:
        return False

    @cached_property
    def asexception(self) -> BaseException:
        if self.error:
            return self.error
        else:
            return Exception(str(self))

    def getvalue(self, strict: bool = True) -> _T | NoReturn:
        if not strict:
            return self.default
        raise self.asexception

    def setvalue(self, newval: _T, store: Optional[str] = None, strict: bool = True) -> None:
        if not strict:
            if store:
                self.metadata[store] = self.default
            self.default = newval
            return
        raise self.asexception

    def __getattr__(self, key: str) -> Any:
        try:
            return self.metadata[key]
        except (TypeError, KeyError):
            raise AttributeError(key) from None


type Result[_T] = Ok[_T] | Err


class EmptyMapping[_K, _V](typing.Mapping[_K, _V]):
    def __len__(self) -> int:
        return 0

    def __iter__(self) -> typing.Iterator[_K]:
        yield from ()

    def __getitem__(self, item: _K) -> _V:
        raise KeyError()


_P = ParamSpec('_P')


def get_result[_T](func: Callable[_P, _T],
                   args: _P.args = (),
                   kwargs: _P.kwargs = EmptyMapping(),
                   *,
                   silent: bool = False,
                   stdout: Optional[IO] = None,
                   stderr: Optional[IO] = None,
                   strict: bool = True,
                   default: Any = None,
                   metadata: Optional[dict] = None,
                   ) -> Result[_T]:
    stdout, stderr, ctx = redirect_outputs(silent, stdout, stderr, strict, wrap_err=Err)
    if isinstance(ctx, Err):
        return ctx

    metadata = dict(metadata) if metadata else {}
    with ctx:
        try:
            value = func(*args, **kwargs)
            metadata.update(stdout=stdout, stderr=stderr)
            return Ok(value, metadata=metadata)

        except BaseException as ex:
            if not strict:
                metadata = dict(get_result=(func, args, kwargs))
                return Err(error=ex, stdout=stdout, stderr=stderr, default=default, metadata=metadata)
            raise


# def as_result(func=None):
#     def _wrapper(fn):
#         @functools.wraps(fn)
#         def _wrapped(*args,
#                      result_silent: bool = False,
#                      result_stdout: Optional[IO] = None,
#                      result_stderr: Optional[IO] = None,
#                      result_strict: bool = True,
#                      result_default: Any = None,
#                      result_metadata: Optional[dict] = None,
#                      **kwargs,
#                      ):
#             return get_result(
#                 fn,
#                 args,
#                 kwargs,
#                 silent=result_silent,
#                 stdout=result_stdout,
#                 stderr=result_stderr,
#                 strict=result_strict,
#                 default=result_default,
#                 metadata=result_metadata,
#             )
#         return _wrapped
#     return _wrapper if func is None else _wrapper(func)
