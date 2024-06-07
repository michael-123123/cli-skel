"""
Utilities to manage context managers.
"""


__all__ = [
    'enable_if',
    'compose_context_managers',
    'redirect_outputs',
]


import io
import os
import pathlib
import sys
from contextlib import contextmanager, ExitStack, redirect_stdout, redirect_stderr
from typing import ContextManager, Iterable, IO, Optional, Callable


@contextmanager
def enable_if(ctx: Iterable[ContextManager], enable: bool):
    """ compose all context managers in ctx if enable is True,
        otherwise - this context manager does nothing.

        Example,
            >>> class A:
            ...     def __enter__(self, *_):
            ...         print("Hi")
            ...     def __exit__(self, *_):
            ...         print("Bye")
            >>> with enable_if([A(), A()], enable=True):
            ...     print("Here")
            Hi
            Hi
            Here
            Bye
            Bye
            >>> with enable_if([A(), A()], enable=False):
            ...     print("Here")
            Here
    """
    stack = ExitStack()
    try:
        if enable:
            _ = [stack.enter_context(c) for c in ctx]
        yield
    finally:
        stack.close()


@contextmanager
def compose_context_managers(context_managers: Iterable[ContextManager]) -> ContextManager:
    """ compose multiple context managers that should
        enter / exit sequentially.

        Example:
            >>> class A:
            ...     def __enter__(self, *_):
            ...         print("Hi")
            ...     def __exit__(self, *_):
            ...         print("Bye")
            >>> with compose_context_managers([A(), A(), A()]):
            ...     print("Here")
            Hi
            Hi
            Hi
            Here
            Bye
            Bye
            Bye
    """
    stack = ExitStack()
    try:
        _ = [stack.enter_context(ctx) for ctx in context_managers]
        yield stack
    finally:
        stack.close()


def bind_stream(stream, silent, strict) -> tuple[IO, Optional[BaseException], bool]:
    """
    returns (stream, exception | None, use_stream_as_ctx_manager?)
    for example, if the stream is a file that was opened by bind_stream,
    we typically want to have use_stream_as_ctx_manager to be True.
    So that the stream is close()d after redirection.
    """

    if silent and stream is None:
        try:
            stream = open(os.devnull, 'w')
        except (OSError, ValueError) as e:
            if not strict:
                return stream, e, True
            raise
        return stream, None, True
    elif isinstance(stream, pathlib.Path):
        try:
            stream = open(stream, 'a')
        except (OSError, ValueError) as e:
            if not strict:
                return stream, e, False
            raise
        return stream, None, True
    elif stream == str:
        return io.StringIO(), None, False

    return stream, None, False


def redirect_outputs[_T](silent: bool = False,
                         stdout: Optional[IO | type[str]] = None,
                         stderr: Optional[IO | type[str]] = None,
                         strict: bool = False,
                         wrap_err: Optional[Callable[..., _T]] = None,
                         ) -> tuple[Optional[IO], Optional[IO], ContextManager | _T]:
    """
    Based on the parameter configuration - perform redirections of stdout and stderr.
    If stdout (resp. stderr) are None then redirection depends on silent. If silent is
    True, stdout (stderr) will be redirected to `os.devnull`. Otherwise, they will not
    be redirected. If stdout (stderr) is the type `str` then an `io.StringIO` redirection
    of stdout (stderr) will be done. Otherwise, stdout (stderr) must be a valid IO handle.

    If strict is True and any errors occur -- then the exceptions are raised.
    If strict is False -- the errors are silenced, and a tuple is returned instead.

    In case os success the return value is the tuple `stdout, stderr, ctx`,
    where stdout and stderr are the redirections of the standard output and error.
    If no redirection is done - these will be None. And `ctx` is a context manager
    which will do redirection and cleanup when entered.

    Typical use case:
        >>> import sys
        >>> out, err, c = redirect_outputs(stderr=str)
        >>> with c:
        ...     print("hello")
        ...     print("world", file=sys.stderr)
        hello
        >>> print(err.getvalue().strip())  # noqa
        world

    :param silent:
    :param stdout:
    :param stderr:
    :param strict:
    :param wrap_err:
    :return:
    """

    stdout = sys.stdout if stdout is None and not silent else stdout
    stdout, stdout_err, close_stdout = bind_stream(stdout, silent, strict)
    if stdout_err:
        return None, None, (wrap_err(stdout_err) if callable(wrap_err) else stdout_err)

    stderr = sys.stderr if stderr is None and not silent else stderr
    stderr, stderr_err, close_stderr = bind_stream(stderr, silent, strict)
    if stderr_err:
        if close_stdout:
            stdout.close()
        return None, None, (wrap_err(stderr_err) if callable(wrap_err) else stderr_err)

    ctx = compose_context_managers([
        enable_if([stdout], enable=close_stdout),
        enable_if([stderr], enable=close_stderr),
        enable_if([redirect_stdout(stdout), redirect_stderr(stderr)], enable=any([silent, stdout, stderr]))
    ])
    return stdout, stderr, ctx
