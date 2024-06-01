"""
convert a cli skeleton dict into a cmd.Cmd class

a cli skeleton dict is a python dictionary that describes the
structure of a command line application. This module contains
utilities that facilitate to define and parse such dictionaries
and obtain cli command loops.

see example in the end of the module.
"""


__all__ = [
    'SkelCmdBase',
    'skel_to_cmd_cls',
]


import argparse
import cmd
import operator
import os
import readline
import shlex
import sys
from typing import ClassVar, Optional, NoReturn, IO, Any, Mapping

from cli_skel.argparse_skel import skel_to_argparse, print_skel, SkelSpecialKeys
from cli_skel.utils.result import Ok, Err, Result, get_result


class SkelCmdBase(cmd.Cmd):
    """
    Base class used by cli skeleton based command loops.
    Generates a class which implements a REPL whose behavior is determined by the cli skeleton.
    """

    EXIT_SUCCESS: ClassVar[int] = 0
    EXIT_FAILURE: ClassVar[int] = 1

    # internal_cmd_prefix: ClassVar[str] = '/'
    internal_cmd_prefix: str = '<>'

    outro: Optional[str] = None

    skel: dict
    skel_parser: argparse.ArgumentParser = None
    skel_actions: dict[str | tuple, argparse.Action | argparse.ArgumentParser | dict] = None

    # noinspection PyPep8Naming
    class _default_config:
        parser: Optional[argparse.ArgumentParser] = None
        auto_dest: Optional[str] = 'toplevel'
        auto_required: bool = True
        skel_params: Any = SkelSpecialKeys
        argparse_kwargs: dict = {}

    skel_config: Any = _default_config

    exit_on_eof: bool = True
    ignore_empty: bool = True

    # init

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)

        if not self.skel_parser or not self.skel_actions:
            argparsed = skel_to_argparse(
                skel=self.skel,
                parser=self.skel_config.parser,
                auto_dest=self.skel_config.auto_dest,
                auto_required=self.skel_config.auto_required,
                **{'prog': '', **self.skel_config.argparse_kwargs},
            )

            self.skel_parser = argparsed.getvalue()
            self.skel_actions = argparsed.metadata['actions']

        if self.exit_on_eof:
            self.do_EOF = self.exit
            self.help_EOF = lambda *_: 'Exit cmd line loop when encountering end-of-file'

        if self.ignore_empty:
            self.emptyline = self._ignore_emptyline

        if not self.skel_config:
            self.skel_config = self._default_config
        else:
            for key, value in vars(self._default_config).items():
                if not hasattr(self.skel_config, key):
                    setattr(self.skel_config, key, value)

    # completion and tokenization

    def _ignore_emptyline(self):
        pass

    # exit

    def exit(self, exit_code: int = EXIT_SUCCESS, *args, **kwargs) -> NoReturn:  # noqa
        try:
            self.postloop()
        except:  # noqa
            pass
        raise SystemExit(exit_code)

    def abort(self, exit_code: int = EXIT_FAILURE, *args, **kwargs) -> NoReturn:
        return self.exit(exit_code, *args, **kwargs)

    # read

    def read(self,
             line: str | list[str],
             *,
             silent: bool = False,
             stdout: Optional[IO | type[str]] = None,
             stderr: Optional[IO | type[str]] = None,
             strict: bool = False,
             ) -> Result[argparse.Namespace]:

        args = self.split_line(line) if isinstance(line, str) else line
        return get_result(
            self.skel_parser.parse_args,
            (args,),
            {},
            silent=silent,
            stdout=stdout,
            stderr=stderr,
            strict=strict,
        )

    # eval

    # noinspection PyMethodMayBeStatic
    def _print_eval_err(self, stdout, stderr) -> None:
        out = stdout.getvalue().strip()
        if out:
            print(out, flush=True)

        err = stderr.getvalue().strip()
        if err:
            err = err.replace('\n: error:', '\nerror:')
            print(err, file=sys.stderr, flush=True)

    def eval(self,
             line: str | list[str],
             name: Optional[str] = None,
             *,
             silent: bool = False,
             stdout: Optional[IO | type[str]] = None,
             stderr: Optional[IO | type[str]] = None,
             strict: bool = False,
             ) -> Result[Any]:
        args = [name] if name is not None else []
        args = [*args, *(self.split_line(line) if isinstance(line, str) else line)]
        read = self.read(args, strict=False, stdout=str, stderr=str)
        match read:
            case Ok(value=value):
                target = getattr(value, self.skel_config.skel_params.TARGET_NAME, None)
                if not callable(target):
                    print(
                        f"Warning: could not find target to run for "
                        f"`{line if isinstance(line, str) else self.join_line(line)}`"
                    )
                    return Err(
                        error=Exception("could not find target to run"),
                        metadata={'args': args, 'parsed': value}
                    )

                return get_result(
                    target,
                    (value,),
                    {},
                    silent=silent,
                    stdout=stdout,
                    stderr=stderr,
                    strict=strict,
                )

            case Err(error=error, stdout=stdout, stderr=stderr):
                if not isinstance(error, SystemExit) or error.code != 0:
                    print(
                        f"error: could not evaluate `{line if isinstance(line, str) else self.join_line(line)}`",
                        file=sys.stderr,
                        flush=True
                    )

                self._print_eval_err(stdout, stderr)
                return read

    def internal_eval(self, line: str) -> Result[Any] | Any:
        toks = self.split_line(line)
        match toks:
            # env control
            case ['env', *rest]:
                self._internal_eval_env(rest)

            # skel printout
            case ['skel' | 'skel-actions' as req]:
                if req == 'skel':
                    print_skel(self.skel)
                else:
                    print_skel(self.skel_actions)

            # usage / help
            case ['usage' | 'help' as req, *rest]:
                self._internal_eval_help(req, rest)

            # parse only
            case ['read' | 'parse', *rest]:
                parsed = self.read(self.join_line(rest), stdout=str, stderr=str)
                print(parsed)
                if parsed.is_err():
                    self._print_eval_err(parsed.stdout, parsed.stderr)

            # eval
            case ['eval', *rest]:
                self.eval(rest)

            # hist
            case [n] if n.isdigit():
                n = int(n)
                histlen = readline.get_current_history_length()
                if histlen > 0:
                    readline.remove_history_item(histlen-1)
                    histlen -= 1
                if 0 < n <= histlen:
                    self.onecmd(readline.get_history_item(n))
                else:
                    print(f'error: {n} -- command not found', file=sys.stderr, flush=True)

            case ['hist']:
                histlen = readline.get_current_history_length()
                histjust = len(str(histlen))
                for i in range(histlen):
                    print(f'{i+1:>{histjust}}  {readline.get_history_item(i+1)}')

            # leave
            case ['exit' | 'quit', *rest]:
                if not rest:
                    return True

                try:
                    code, *_ = rest
                    code = int(code)
                except:  # noqa
                    self.abort()
                self.exit(code)

            case _:
                return super().default(f'{self.internal_cmd_prefix}{line}')

    # noinspection PyMethodMayBeStatic
    def _internal_eval_env(self, toks):
        def printenv(dct: Any):
            items = dct.items() if isinstance(dct, Mapping) else dct
            print('\n'.join(f'\t{k}={v!r}' for k, v in items))

        def modify_env(k: str, v: str) -> str:
            if v is not missing:
                os.environ[k] = v
            elif k.startswith('!'):
                k = k.removeprefix('!')
                os.environ.pop(k, None)
            return k

        missing = object()
        match toks:
            # env control
            case []:
                printenv(os.environ)
            case ['-s']:
                env = sorted(os.environ.items(), key=operator.itemgetter(0))
                printenv(env)
            case _:
                sort = toks and toks[0].strip() == '-s'
                toks = toks[sort:]
                toks = [tok.split('=', maxsplit=1) for tok in toks]
                toks = [[*tok, missing][:2] for tok in toks]
                toks = sorted(toks, key=operator.itemgetter(0)) if sort else toks
                for key, value in toks:
                    key = modify_env(key, value)
                    value = os.environ.get(key)
                    value = value if value is None else f'{value!r}'
                    print(f'\t{key}={value}')

    def _internal_eval_help(self, kind: str, toks: list):
        def print_all_usage(p):
            print(p[self.skel_config.skel_params.INIT].format_usage().strip())
            for nc, c in p.get(self.skel_config.skel_params.SUBPARSERS, {}).items():
                if nc != self.skel_config.skel_params.INIT:
                    print_all_usage(c)

        if kind == 'usage' and toks and toks[0].strip() == '-a':
            print_all_usage(self.skel_actions)
            return

        toplevel = self.skel_actions
        for tok in toks:
            toplevel = toplevel.get(self.skel_config.skel_params.SUBPARSERS, {}).get(tok, {})

        parser = toplevel.get(self.skel_config.skel_params.INIT, self.skel_parser)
        fmt = parser.format_usage() if kind == 'usage' else parser.format_help()
        print(fmt.replace('\n: ', '\n').strip())

    def default(self, line):
        if line.startswith(self.internal_cmd_prefix):
            return self.internal_eval(line.removeprefix(self.internal_cmd_prefix))
        else:
            return self.internal_eval(f'eval {line}')
        # else:
        #     return super().default(line)

    def postcmd(self, stop, line):
        match stop:
            case Ok() | Err():
                return False
            case _:
                return super().postcmd(stop, line)

    # loop

    def postloop(self):
        if self.outro:
            print(self.outro)

    # help / usage

    def do_help(self, arg):
        return self.internal_eval(f'help {arg}'.strip())

    @classmethod
    def split_name(cls, line: str) -> tuple[str, list[str]]:
        name, *rest = line.split(maxsplit=1)
        return name, rest

    @classmethod
    def split_line(cls, line: str) -> list[str]:
        return shlex.split(line)

    @classmethod
    def join_line(cls, toks: list[str]) -> str:
        return shlex.join(toks)


def skel_to_cmd_cls(skel: dict[str, str | dict],
                    *,
                    intro: Optional[str] = None,
                    outro: Optional[str] = None,
                    prompt: Optional[str] = None,
                    ignore_empty: bool = True,
                    exit_on_eof: bool = True,
                    internal_cmd_prefix: str = '<>',
                    skel_params: Any = SkelSpecialKeys,
                    parser: Optional[argparse.ArgumentParser] = None,
                    auto_dest: Optional[str] = 'toplevel',
                    auto_required: bool = True,
                    **argparse_kwargs,
                    ) -> type[cmd.Cmd]:
    """
    function that takes a cli skeleton and returns a class which is an
    instance of cmd.Cmd and implements behavior based on that cli skeleton.
    """

    skel_ = skel

    intro_ = intro
    outro_ = outro
    prompt_ = prompt

    internal_cmd_prefix_ = internal_cmd_prefix
    ignore_empty_ = ignore_empty
    exit_on_eof_ = exit_on_eof

    class SkelCmd(SkelCmdBase):
        internal_cmd_prefix = internal_cmd_prefix_

        intro: Optional[str] = intro_
        outro: Optional[str] = outro_
        prompt: Optional[str] = prompt_

        skel = skel_
        skel_config = argparse.Namespace(
            parser=parser,
            auto_dest=auto_dest,
            auto_required=auto_required,
            skel_params=skel_params,
            argparse_kwargs=argparse_kwargs,
        )

        exit_on_eof = exit_on_eof_
        ignore_empty = ignore_empty_

    return SkelCmd


def skel_to_cmd(skel: dict[str, str | dict],
                *,
                intro: Optional[str] = None,
                outro: Optional[str] = None,
                prompt: Optional[str] = None,
                ignore_empty: bool = True,
                exit_on_eof: bool = True,
                internal_cmd_prefix: str = '<>',
                skel_params: Any = SkelSpecialKeys,
                parser: Optional[argparse.ArgumentParser] = None,
                auto_dest: Optional[str] = 'toplevel',
                auto_required: bool = True,
                **argparse_kwargs,
                ) -> cmd.Cmd:
    cmd_cls = skel_to_cmd_cls(
        skel=skel,
        intro=intro,
        outro=outro,
        prompt=prompt,
        ignore_empty=ignore_empty,
        exit_on_eof=exit_on_eof,
        internal_cmd_prefix=internal_cmd_prefix,
        skel_params=skel_params,
        parser=parser,
        auto_dest=auto_dest,
        auto_required=auto_required,
        **argparse_kwargs,
    )
    return cmd_cls()


# TODO: add support for ?? which will do internal command support and help
#       for example ?? will print the current config etc and show internal command structure
#       and `?? cmd` will provide help for it.


"""
    def find_abbrev(self, line: str) -> str:
        line = line.strip()
        if not line:
            return line

        try:
            help_prefix = ''
            name, rest = self.split_name(line)
            if name in ['help']:
                if not rest:
                    return line
                help_prefix = 'help '
                name, rest = self.split_name(line[4:].strip())

            names = [func[3:] for func in vars(type(self)) if func.startswith(f'do_{name}')]
            if 1 == len(names) and name != names[0]:
                name = names[0]

            return help_prefix + (' '.join([name, *rest]))

        except (ValueError, TypeError):
            return line





    # def default(self, line):
    #     try:
    #         name, *line = line.split(maxsplit=1)
    #         ns = self.template_do_cmd(name, line[0] if line else '')
    #         print(ns)
    #     except BaseException as e:
    #         print(e, file=sys.stderr)
"""
# cmd_parser.error('asdasdas')

"""

        # if abbrev_cmd:
        #     def precmd(self, line: str) -> str:
        #         line = self.find_abbrev(line)
        #         return super().precmd(line)
        """


"""
            # case ['arg', *rest]:
            #     missing = object()
            #     rest = [tok.split('=', maxsplit=1) for tok in rest]
            #     rest = [[*tok, missing][:2] for tok in rest]
            #     rest = sorted(rest, key=operator.itemgetter(0))
            #     for key, value in rest:
            #         if value is not missing:
            #             self.skel_parser.set_defaults(key=value)
            #         elif key.startswith('!'):
            #             key = key.removeprefix('!')
            #             self.skel_parser.set_defaults(key=None)
            #
            #         value = self.skel_parser.get_default(key)
            #         value = value if value is None else f'{value!r}'
            #         print(f'\t{key}={value}')

"""

# # from eval()
# stdout, stderr, ctx = self._setup_output_redirection(silent, stdout, stderr, strict)
# if isinstance(ctx, Err):
#     return ctx
#
# with ctx:
#     try:
#         evald = target(value)
#         return Ok(evald, metadata=dict(stdout=stdout, stderr=stderr))
#     except BaseException as e:
#         if not strict:
#             return Err(e, stdout=stdout, stderr=stderr)
#         raise

# # noinspection PyMethodMayBeStatic
# def _setup_output_redirection(self,
#                               silent: bool = False,
#                               stdout: Optional[IO | type[str]] = None,
#                               stderr: Optional[IO | type[str]] = None,
#                               strict: bool = False,
#                               ) -> tuple[Optional[IO], Optional[IO], ContextManager | Err]:
#     stdout, stdout_err, close_stdout = bind_stream(stdout, silent, strict)
#     if stdout_err:
#         return None, None, Err(stdout_err)
#
#     stderr, stderr_err, close_stderr = bind_stream(stderr, silent, strict)
#     if stderr_err:
#         if close_stdout:
#             stdout.close()
#         return None, None, Err(stderr_err)
#
#     ctx = compose_context_managers([
#         enable_if([stdout], enable=close_stdout),
#         enable_if([stderr], enable=close_stderr),
#         enable_if([redirect_stdout(stdout), redirect_stderr(stderr)], enable=any([silent, stdout, stderr]))
#     ])
#     return stdout, stderr, ctx

# # from read()
# stdout, stderr, ctx = self._setup_output_redirection(silent, stdout, stderr, strict)
# if isinstance(ctx, Err):
#     return ctx
#
# with ctx:
#     args = self.split_line(line) if isinstance(line, str) else line
#     try:
#         namespace = self.skel_parser.parse_args(args)
#         return Ok(namespace, metadata=dict(stdout=stdout, stderr=stderr))
#     except BaseException as e:
#         if not strict:
#             return Err(e, stdout=stdout, stderr=stderr)
#         raise
