"""
convert a cli skeleton dict into an argparse.ArgumentParser

a cli skeleton dict is a python dictionary that describes the
structure of a command line application. This module contains
utilities that facilitate to define and parse such dictionaries
and obtain the argument parsers.

see example in the end of the module.
"""


__all__ = [
    'SkelSpecialKeys',
    'skel_to_argparse',
    'skel_to_actions',
    'print_skel',
    'format_skel',
    'set_skel_defaults',
    'iter_skel_positionals_defaults',
    'BooleanFlag',
]


import argparse
from copy import deepcopy
from typing import Optional, IO, Any, Generator, Iterable

from cli_skel.utils.result import Result, get_result
from cli_skel.utils.sentinels import MissingType


_MISSING = MissingType(__name__)


class SkelSpecialKeys:
    """
    a class defining the constants used.
    this may be user defined (see the `skel_params` argument)
    """
    INIT: tuple = ()
    SUBPARSERS: str = '_'
    TARGET: str = '->'
    TARGET_NAME: str = 'target_'


def skel_to_argparse(skel: dict[str | tuple, str | dict],
                     parser: Optional[argparse.ArgumentParser] = None,
                     *,
                     auto_dest: Optional[str] = 'toplevel',
                     auto_required: bool = True,
                     skel_params: Any = SkelSpecialKeys,
                     silent: bool = False,
                     stdout: Optional[IO] = None,
                     stderr: Optional[IO] = None,
                     strict: bool = True,
                     default: Any = None,
                     **argparse_kwargs,
                     ) -> Result[argparse.ArgumentParser]:
    """
    Convert a cli skeleton dict to a Result object holding an ArgumentParser on success.
    """

    argparsed = skel_to_actions(
        skel,
        parser,
        auto_dest=auto_dest,
        auto_required=auto_required,
        skel_params=skel_params,
        silent=silent,
        stdout=stdout,
        stderr=stderr,
        strict=strict,
        default=default,
        **argparse_kwargs,
    )

    if argparsed.is_ok():
        actions = argparsed.getvalue()
        argparsed.setvalue(actions[skel_params.INIT], store='actions')

    return argparsed


def skel_to_actions(skel: dict[str | tuple, str | dict],
                    parser: Optional[argparse.ArgumentParser] = None,
                    *,
                    auto_dest: Optional[str] = 'toplevel',
                    auto_required: bool = True,
                    skel_params: Any = SkelSpecialKeys,
                    silent: bool = False,
                    stdout: Optional[IO] = None,
                    stderr: Optional[IO] = None,
                    strict: bool = True,
                    default: Any = None,
                    **argparse_kwargs,
                    ) -> Result[argparse.ArgumentParser]:
    """
    Convert a cli skeleton dict to a Result object holding the same structure skeleton dict,
    where each key in the skeleton points to its corresponding argparse Action.
    """

    return get_result(
        skel_to_actions_,
        args=[skel, parser],
        kwargs={
            'auto_dest': auto_dest,
            'auto_required': auto_required,
            'skel_params': skel_params,
            **argparse_kwargs,
        },
        silent=silent,
        stdout=stdout,
        stderr=stderr,
        strict=strict,
        default=default,
    )


def skel_to_actions_(skel: dict[str | tuple, str | dict],
                     parser: Optional[argparse.ArgumentParser] = None,
                     *,
                     auto_dest: Optional[str] = 'toplevel',
                     auto_required: bool = True,
                     skel_params: Any = SkelSpecialKeys,
                     **argparse_kwargs,
                     ) -> dict[str | tuple, dict | argparse.Action | argparse.ArgumentParser]:
    skel = deepcopy(skel)
    if parser is None:
        parser_kwargs = {**skel.pop(skel_params.INIT, {}), **argparse_kwargs}
        parser = argparse.ArgumentParser(**parser_kwargs)

    skel_to_argparse_kwargs = dict(auto_dest=auto_dest, auto_required=auto_required, skel_params=skel_params)
    skel_actions = skel_to_argparse_actions(skel, parser, **skel_to_argparse_kwargs)
    return skel_actions


def skel_to_argparse_actions(skel: dict[str | tuple, str | dict],
                             parser: Optional[argparse.ArgumentParser] = None,
                             *,
                             auto_dest: Optional[str] = '',
                             auto_required: bool = True,
                             skel_params: Any = SkelSpecialKeys,
                             ) -> dict[str | tuple, dict | argparse.Action]:
    skel_actions = {skel_params.INIT: parser}

    target = skel.pop(skel_params.TARGET, _MISSING)
    if target is not _MISSING:
        parser.set_defaults(**{skel_params.TARGET_NAME: target})

    subskel = skel.pop(skel_params.SUBPARSERS, _MISSING)

    for argname, arg_params in skel.items():
        argnames = (argname,) if isinstance(argname, str) else argname
        arg_explicit_params = arg_params.pop(skel_params.INIT, {})
        arg_params = {**arg_explicit_params, **arg_params}
        action = parser.add_argument(*argnames, **arg_params)
        skel_actions[argname] = action

    if subskel is not _MISSING:
        subparsers_kwargs = subskel.pop(skel_params.INIT, {})

        if auto_dest is not None:
            cmd_dest = f'{auto_dest}_dest'
            subparsers_kwargs.setdefault('dest', cmd_dest)
        if auto_required:
            subparsers_kwargs.setdefault('required', True)

        subparsers = parser.add_subparsers(**subparsers_kwargs)
        skel_subactions = {skel_params.INIT: subparsers}
        skel_actions[skel_params.SUBPARSERS] = skel_subactions

        for subcmd, subcmd_params in subskel.items():
            subparser_kwargs = subcmd_params.pop(skel_params.INIT, {})
            subparser = subparsers.add_parser(**{**{'name': subcmd}, **subparser_kwargs})
            skel_subactions[subcmd] = skel_to_argparse_actions(
                subcmd_params,
                subparser,
                auto_dest=None if auto_dest is None else subcmd,
                auto_required=auto_required
            )

    return skel_actions


# noinspection PyPep8Naming
def BooleanFlag(default=True, **kwargs):
    """
    a shortcut to define --flag --no-flag type arguments for argparse cli skeletons.

    :param default:
    :param kwargs:
    :return:
    """
    return {
        'default': default,
        'action': argparse.BooleanOptionalAction,
        **{'type': bool, **kwargs},
    }


def iter_skel_positionals_defaults(skel: dict,
                                   skel_params: Any = SkelSpecialKeys
                                   ) -> Generator[tuple[str, bool], None, None]:
    skel.pop(skel_params.INIT, None)
    skel.pop(skel_params.TARGET, None)

    for arg, arginfo in skel.items():
        if arg == skel_params.SUBPARSERS:
            arginfo.pop(skel_params.INIT, None)
            arginfo.pop(skel_params.TARGET, None)
            for _, subarginfo in arginfo.items():
                yield from iter_skel_positionals_defaults(subarginfo)
        else:
            if isinstance(arg, str):
                arg = arg,

            arg = arg[0]
            if not arg.startswith('-'):
                yield arg, arginfo.get('default', _MISSING)


def set_skel_defaults(parser: argparse.ArgumentParser,
                      skel: dict,
                      default: Any = _MISSING,
                      lookup: Optional[dict] = None,
                      ) -> None:
    lookup = {} if lookup is None else lookup
    defaults = {arg: lookup.get(arg, default)
                for arg, hasdef in iter_skel_positionals_defaults(skel)
                if hasdef is _MISSING and parser.get_default(arg) is None
                }
    parser.set_defaults(**defaults)


def print_skel(dct: dict, indent: int = 2) -> None:
    """
    pretty print a cli skeleton dict
    """
    print(format_skel(dct, indent))


def format_skel(dct: dict, indent: int = 2) -> str:
    """
    pretty format a cli skeleton dict
    """
    space = (' ' * indent) if isinstance(indent, int) else str(indent)
    return format_skel_(dct, '', space)


def format_skel_(dct: dict, space: str, space_incr: str) -> str:
    fmt = ['{']
    for key, value in dct.items():
        if isinstance(value, dict):
            if not value:
                fmt.append(f'{space}{space_incr}{key!r}: {value!r},')
            elif (1 == len(value) and
                  (isinstance(next_value := next(iter(value.values())), str) or not isinstance(next_value, Iterable))):
                fmt.append(f'{space}{space_incr}{key!r}: {value!r},')
            else:
                fmt_value = format_skel_(value, space + space_incr, space_incr)
                fmt.append(f'{space}{space_incr}{key!r}: {fmt_value},')

        else:
            fmt.append(f'{space}{space_incr}{key!r}: {value!r},')
    fmt.append(f'{space}' + '}')
    return '\n'.join(fmt)
