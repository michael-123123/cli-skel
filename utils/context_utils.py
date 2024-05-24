"""
Utilities to manage context managers.
"""


__all__ = [
    'enable_if',
    'compose_context_managers',
]


from contextlib import contextmanager, ExitStack
from typing import ContextManager, Iterable


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
