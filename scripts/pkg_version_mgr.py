"""
Manage the version number from a `pyproject.toml` file.
Depends on installing `tomlkit`.
"""

import argparse
import pathlib
import sys
from typing import Optional

from tomlkit import dump, load, table


def to_version_tuple(version: str, maxsplit=None) -> list[tuple[Optional[int], Optional[str]]]:
    version = version.split('.') if maxsplit is None else version.split('.', maxsplit=maxsplit)
    rest = (None, version.pop() if maxsplit and len(version) > maxsplit else None)

    version_tuples = []
    for v in version:
        p = next((i for i, c in enumerate(v) if c not in '0123456789'), len(v))
        n, s = v[:p], v[p:]
        n = None if not n else int(n)
        s = None if not s else s
        version_tuples.append((n, s))

    if rest != (None, None):
        version_tuples.append(rest)

    return version_tuples


def is_valid_version_tuple(version_tuples: list[tuple[Optional[int], Optional[str]]]) -> bool:
    # a three valued version
    if len(version_tuples) != 3:
        return False

    (major, major_s), (minor, minor_s), (patch, patch_s) = version_tuples

    # major version is int
    if major is None or major_s is not None:
        return False

    # minor version is int
    if minor is None or minor_s is not None:
        return False

    # patch is int + optional suffix which is free text
    if patch is None:
        return False

    return True


def _parser(progname=None):
    progname = pathlib.Path(sys.argv[0]).stem if progname is None else progname
    parser = argparse.ArgumentParser(prog=progname)

    parser.add_argument(
        '--pyproject',
        default='pyproject.toml',
        help='path to pyproject.toml file'
    )

    action = parser.add_subparsers(
        title='action to do',
        help='select which action will be performed on pyproject.toml version variable',
        dest='action',
        required=True,
    )

    action.add_parser(
        'get',
        help='get the current version'
    )

    setter = action.add_parser(
        'set',
        help='set the current version'
    )
    setter.add_argument('version', help='a semantic version tuple in the form <int>.<int>.<int>')
    setter.add_argument('--force', help='skip validation of version', type=bool, action=argparse.BooleanOptionalAction)

    incr = action.add_parser(
        'incr',
        aliases=['increment', 'increase'],
        help='increase the current version',
    )
    incr.add_argument(
        '--part',
        choices=['major', 'minor', 'patch'],
        help='which version part to increment. less dominant parts are zeroed out',
        default='patch',
    )
    incr.add_argument(
        '--suffix',
        help='add suffix to the patch portion of the version',
        default=None
    )

    return parser


def _main(progname=None, args=None):
    parser = _parser(progname)
    ns = parser.parse_args(args)

    tomlfile = pathlib.Path(ns.pyproject)
    if not tomlfile.exists() or not tomlfile.is_file():
        parser.error(f'could not find file `{tomlfile!r}`')
        sys.exit(1)

    with open(tomlfile, 'r') as fd:
        toml = load(fd)

    if ns.action == 'get':
        version = toml.get('project', {}).get('version', None)
        if version is not None:
            print(version)
    elif ns.action == 'set':
        version_str = ns.version
        version = to_version_tuple(version_str, maxsplit=3)
        if not is_valid_version_tuple(version):
            parser.error(f'version `{version_str}` is not a valid version tuple')
            sys.exit(1)

        toml.setdefault('project', table())
        toml['project']['version'] = version_str
        with open(tomlfile, 'w') as fd:
            dump(toml, fd)
    elif ns.action == 'incr':
        version = toml.get('project', {}).get('version', None)
        version = to_version_tuple(version, maxsplit=3) if version is not None else [(0, None), (0, None), (1, None)]
        if not is_valid_version_tuple(version):
            parser.error(f'pyproject.toml seems to have an invalid version tuple - will not update')
            sys.exit(1)

        (major, _), (minor, _), (patch, oldsuffix) = version
        part, suffix = ns.part, ns.suffix
        suffix = suffix if suffix is not None else oldsuffix
        suffix = suffix if suffix is not None else ''

        if part == 'major':
            version = (major + 1, 0, 0)
        elif part == 'minor':
            version = (major, minor + 1, 0)
        elif part == 'patch':
            version = (major, minor, patch + 1, )
        else:
            parser.error(f'unknown operation `incr {part}`')
            sys.exit(1)

        version = '.'.join([str(x) for x in version])
        version += suffix

        toml.setdefault('project', table())
        toml['project']['version'] = version

        with open(tomlfile, 'w') as fd:
            dump(toml, fd)
    else:
        parser.error(f'unknown action `{ns.action}`')


if __name__ == '__main__':
    _main()
