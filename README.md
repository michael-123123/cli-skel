# CLI Skeleton Library

Generate CLI application from python dictionaries.

A **cli-skeleton** is a python dictionary which describes the structure of a command line application.
This library may convert a cli-skeleton into either an `ArgumentParser` or a `Cmd` object.

If you write a lot of command line applications - this library can help reduce the time you spend 
writing boilerplate `argparse` and `cmd` code.


## Usage

```python
import cli_skel

print(cli_skel.__version__)
```


### Example 1: A Basic CLI Parser

```python
from cli_skel.argparse_skel import skel_to_argparse

skel = {
    'filenames': {
        'nargs': '+',
        'help': 'Filenames to do something with',
    },
    
    '--log-level': {
        'default': 'warning',
        'choices': {'debug', 'info', 'warning', 'error'},
    },
}

parser = skel_to_argparse(skel).getvalue()
ns = parser.parse_args(['file1', 'file2', 'file3', '--log-level=error'])
```

The dictionary `skel` describes the parameters of a cli application which takes positional parameters
`filenames`, and optional parameter `--log-level`. 

The keys of `skel` are parameter names and their values are dictionaries describing how the 
argument parser should handle them. Specifically, there must be at least one positional `filenames`,
as well as an optional parameter `--log-level` with a default value of `warning` and it may be one of 
four choices.

The code above is equivalent to the following pure-python implementation:
```python
import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    'filenames',
    nargs='+',
    help='Filenames to do something with',
)

parser.add_argument(
    '--log-level',
    default='warning',
    choices=['debug', 'info', 'warning', 'error'],
)

ns = parser.parse_args(['file1', 'file2', 'file3', '--log-level=error'])
```

Additionally, each cli-skeleton may be converted to a `cmd.Cmd` object.
When this object's `onecmd()` is run it will use the skeleton to navigate to the 
appropriate command to run. This notion is covered by later examples.


### Example 2: A More Advanced Use Case

```python
import argparse
from cli_skel.argparse_skel import skel_to_argparse

skel = {
    '--log-file': {
        'default': 'stdout',
        'help': 'output file for logs',
    },
    '--verbose': {
        'default': False,
        'type': bool,
        'action': argparse.BooleanOptionalAction,
    },
    '_': {
        'cmd1': {'->': lambda *_: print('cmd1 is running')},
        'cmd2': {'->': lambda *_: print('cmd2 is running')},
        'cmd3': {
            '--ignore-errors': {
                'type': bool,
                'default': False,
                'action': argparse.BooleanOptionalAction,
            },
            '->': lambda *_: print('cmd3 is running')
        },
    }
}

parser = skel_to_argparse(skel).getvalue()
ns = parser.parse_args(['cmd3', '--ignore-errors'])
ns.target_()
# 'cmd3 is running'
```

In this example `skel` is a cli-skeleton which has two optional parameters `--log-file` and `--verbose`,
and one positional parameter which may be one of `cmd1`, `cmd2` or `cmd3`. The `'_'` denotes a group of 
subparsers which are added when creating the `argparse.ArgumentParser`. Each one of `cmd1`, `cmd2` and `cmd3`
is itself a cli-skeleton. For example, `cmd3` defines the optional parameter `--ignore-errors`. 

The key `'->'` in the definitions of `cmd1`, `cmd2` and `cmd3` is the target key. If the respective command is 
selected, then the target value will be part of its payload. It may be used to dispatch commands. 
In the example above, the `cmd3` is selected. Therefore, the `argparse.Namespace` object which returns from 
`parser.parse_args()` has `target_` set to the value of `skel['_']['cmd3']['->']`.

The code above is equivalent to the following pure-python implementation:
```python
import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    '--log-file',
    default='stdout',
    help='output file for logs',
)

parser.add_argument(
    '--verbose',
    default=False,
    type=bool,
    action=argparse.BooleanOptionalAction,
)

subparsers = parser.add_subparsers(dest='toplevel_dest', required=True)

cmd1 = subparsers.add_parser('cmd1')
cmd1.set_defaults(target_=lambda *_: print('cmd1 is running'))

cmd2 = subparsers.add_parser('cmd2')
cmd2.set_defaults(target_=lambda *_: print('cmd2 is running'))

cmd3 = subparsers.add_parser('cmd3')
cmd3.add_argument(
    '--ignore-errors',
    type=bool,
    default=False,
    action=argparse.BooleanOptionalAction,
)
cmd3.set_defaults(target_=lambda *_: print('cmd3 is running'))

ns = parser.parse_args(['cmd3', '--ignore-errors'])
ns.target_()
```


### Example 3: cli-skeletons and `cmd.Cmd`  


Cli-skeletons may also be converted to `cmd.Cmd` objects.


```python
from cli_skel.cmd_skel import skel_to_cmd

skel = {
    '_': {
        'cmd1': {'->': lambda *_: print('cmd1 is running')},
        'cmd2': {'->': lambda *_: print('cmd2 is running')},
        'cmd3': {
            '--verbose': {'type': bool, 'default': False},
            '->': lambda *_: print('cmd3 is running') },
    }
}

cmd = skel_to_cmd(
    skel,
    intro='hello - welcome...',
    outro='sad to see you go',
    prompt='>> ',
    internal_cmd_prefix='/',
)
cmd.cmdloop()
```
```shell
hello - welcome...
>> cmd1
cmd1 is running
>> cmd3 --verbose
cmd3 is running
>> /exit
sad to see you go
```


## Installation

### Install Directly from PyPI
```shell
pip install cli-skel
```

### Install Latest from GitHub
```shell
pip install 'git+https://github.com/michael-123123/cli-skel.git'
```

### Install From Source
```shell
git clone https://github.com/michael-123123/cli-skel.git
cd cli-skel
pip install .
```


## License

`cli-skel` was created and owned by Michael Frank.

`cli-skel` is licensed under the terms of the MIT license (see [LICENSE](LICENSE) file for details.)
