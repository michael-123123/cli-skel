# TODO: finish this testing


from cli_skel.cmd_skel import skel_to_cmd_cls


def _main():
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
    cls = skel_to_cmd_cls(
        skel,
        intro='hello - welcome...',
        outro='sad to see you go',
        prompt='>>> ',
        internal_cmd_prefix='/',
    )
    cls().cmdloop()


if __name__ == '__main__':
    _main()

