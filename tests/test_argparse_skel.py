import argparse
import unittest

from cli_skel.argparse_skel import skel_to_argparse
from cli_skel.utils.result import Ok, Err, Result, get_result


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


class TestArgparseSkel(unittest.TestCase):
    def test_skel_to_argparse_basics1(self):
        parser = skel_to_argparse(skel).getvalue()
        self.assertTrue(isinstance(parser, argparse.ArgumentParser))

    def test_skel_to_argparse_basics2(self):
        result = skel_to_argparse(skel, strict=False)
        self.assertTrue(isinstance(result, Ok))

        parser = result.getvalue()
        self.assertTrue(isinstance(parser, argparse.ArgumentParser))

        actions = result.metadata['actions']
        self.assertTrue(isinstance(actions, dict))
        self.assertTrue({(), *skel.keys()} == {*actions.keys()})

    def test_skel_to_argparse_basics3(self):
        bad_skel = {
            'positional_param': {
                'required': True
            }
        }
        result = skel_to_argparse(bad_skel, strict=False)
        self.assertTrue(isinstance(result, Err))
        self.assertTrue("'required' is an invalid argument for positionals" == str(result.error))

    def parse_skel_to_argparse(self,
                               argparse_skel: dict,
                               args=()
                               ) -> tuple[Result[argparse.ArgumentParser], Result[argparse.Namespace]]:
        result = skel_to_argparse(argparse_skel, strict=False)
        self.assertTrue(isinstance(result, Ok))

        parser = result.getvalue()
        ns = get_result(parser.parse_args, [args], strict=False)

        return result, ns

    def test_simple_usage(self):
        my_skel = skel
        parser = skel_to_argparse(my_skel).getvalue()
        ns = parser.parse_args(['123', 'Z', 'd', 'pos', 'cmd3', '--a', '321'])
        self.assertTrue(ns.x == 123)
        self.assertTrue(ns.y == 'Z')
        self.assertTrue(ns.toplevel_dest == 'd')
        self.assertTrue(ns.asd == 'pos')
        self.assertTrue(ns.d_dest == 'cmd3')
        self.assertTrue(ns.a == 321)

    def succeed_skel_to_argparse_and_parse(self,
                                           argparse_skel: dict,
                                           params_dict: dict,
                                           ) -> tuple[argparse.ArgumentParser, argparse.Namespace, list]:
        args = [value if isinstance(value, str) else ''.join(value) for value in params_dict.values()]
        parser, ns = self.parse_skel_to_argparse(argparse_skel, args)
        self.assertTrue(isinstance(ns, Ok))

        parser = parser.getvalue()
        ns = ns.getvalue()
        for key, value in params_dict.items():
            value = value if isinstance(value, str) else value[-1]
            self.assertTrue(hasattr(ns, key))
            self.assertTrue(value == str(getattr(ns, key)))

        return parser, ns, args

    def test_to_argparse_usage1(self):
        params = dict(x='123', y='this_is_y', toplevel_dest='d', asd='hello', d_dest='cmd3', a=('--a=', '123'))
        self.succeed_skel_to_argparse_and_parse(skel, params)
