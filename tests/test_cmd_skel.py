import unittest
from contextlib import redirect_stdout
from io import StringIO
from typing import Any

from cli_skel.cmd_skel import skel_to_cmd_cls, SkelCmdBase

skel = {
        'x': {(): {'type': int}, 'help': 'asdasda'},
        'y': {},
        '--z': {},
        '--h': {},
        '_': {
            (): {
                'required': True,
                # 'dest': 'cmd',
            },
            'a': {'->': lambda *_, **__: print('a is running...')},
            'b': {'->': lambda *_, **__: print('b is running...')},
            'c': {'->': lambda *_, **__: print('c is running...')},
            'd': {
                '--w': {},
                'asd': {},
                '_': {
                    'cmd1': {'->': lambda *_, **__: print('d/cmd1 is running...')},
                    'cmd2': {'->': lambda *_, **__: print('d/cmd2 is running...')},
                    'cmd3': {'->': lambda *_, **__: print('d/cmd3 is running...'),
                             '--a': {'type': int},
                             },
                }
            },
        }
    }
"""
prog <x> <y> [--z | --no-z] [--h=hello] {cmd: a b c {d: [--w=world] d1 d2 d3 [--a=abc]}}
    prog x y [optionals] a
    prog x y [optionals] b
    prog x y [optionals] c
    prog x y [optionals] d [optionals_d] d1
    prog x y [optionals] d [optionals_d] d2
    prog x y [optionals] d [optionals_d] d3 [optionals_d3]
"""

CmdClassFromSkel = skel_to_cmd_cls(
    skel,
    intro='hello - welcome...',
    outro='sad to see you go',
    prompt='>>> ',
    internal_cmd_prefix='/',
)
"""
CmdClassFromSkel is a subtype of `cmd.Cmd`
"""


class TestCmdFromSkel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cmd: SkelCmdBase = CmdClassFromSkel()  # noqa

    @classmethod
    def run_one_liner(cls, cmd: SkelCmdBase, args: list) -> Any:
        return cmd.onecmd(cmd.join_line(args))

    @classmethod
    def cleanup_str(cls, s):
        return s.replace(' ', '').replace('\n', '').replace('\t', '')

    def test_help(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            self.run_one_liner(self.cmd, ['-h'])

        out_str = out.getvalue()
        out.close()

        help_msg = """
            usage: [-h] [--z Z] [--h H] x y {a,b,c,d} ...

            positional arguments:
              x           asdasda
              y
              {a,b,c,d}
            
            options:
              -h, --help  show this help message and exit
              --z Z
              --h H
        """

        out_str = self.cleanup_str(out_str)
        help_msg = self.cleanup_str(help_msg)
        self.assertTrue(out_str == help_msg)

    def test_usage(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            self.run_one_liner(self.cmd, ['/usage', '-a'])

        out_str = out.getvalue()
        out.close()

        usage_msg = """
            usage: [-h] [--z Z] [--h H] x y {a,b,c,d} ...
            usage: x y a [-h]
            usage: x y b [-h]
            usage: x y c [-h]
            usage: x y d [-h] [--w W] asd {cmd1,cmd2,cmd3} ...
            usage: x y d asd cmd1 [-h]
            usage: x y d asd cmd2 [-h]
            usage: x y d asd cmd3 [-h] [--a A]
        """

        out_str = self.cleanup_str(out_str)
        usage_msg = self.cleanup_str(usage_msg)
        self.assertTrue(out_str == usage_msg)

    def test_a_cmd(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            self.run_one_liner(self.cmd, ['123', 'Z', 'a'])

        out_str = out.getvalue()
        out.close()

        msg = "a is running..."

        out_str = self.cleanup_str(out_str)
        msg = self.cleanup_str(msg)
        self.assertTrue(out_str == msg)
