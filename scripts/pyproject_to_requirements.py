"""
generate `requirements.txt` files from the dependencies sections of a `pyproject.toml` file.
"""

import argparse
import pathlib
import sys
import tomllib
from typing import Optional


def generate_requirements_files(pyproject_defs: dict,
                                output_dir: pathlib.Path,
                                sections: Optional[list | bool] = False
                                ) -> dict[str, pathlib.Path]:
    requirement_files = {}

    requirements = pyproject_defs.get('dependencies', [])
    with open(output_dir / "requirements.txt", "w") as req_file:
        req_file.writelines([f'{r}\n' for r in requirements])
        requirement_files[None] = output_dir / "requirements.txt"

    if sections is False:
        return requirement_files

    optionals = pyproject_defs.get('optional-dependencies', {})
    if sections is not True:
        bad_sections = {section for section in sections if section not in optionals}
        if bad_sections:
            bad_sections = ', '.join(bad_sections)
            print(f'warning: ignoring unknown requirements sections: {bad_sections}', file=sys.stderr)
        optionals = {key: value for key, value in optionals.items() if key in sections}

    for name, deps in optionals.items():
        with open(output_dir / f"requirements-{name}.txt", "w") as req_file:
            req_file.writelines([f'{r}\n' for r in deps])
            requirement_files[name] = output_dir / f"requirements-{name}.txt"

    return requirement_files


def main(args=None, do_exit: bool = True) -> int:
    if do_exit:
        try:
            _main(args)
        except SystemExit as e:
            return e.code
        except BaseException:  # noqa
            return 1
        return 0
    else:
        _main(args)


def _main(args=None):
    parser = argparse.ArgumentParser(prog=sys.argv[0])

    parser.add_argument(
        '--pyproject',
        default='pyproject.toml',
        help='location of the pyproject.toml file (default is "pyproject.toml")'
    )

    parser.add_argument(
        'requirements',
        nargs='*',
        default=[],
        action='extend',
        help='create requirements-optional.txt file for each of these sections'
    )

    parser.add_argument(
        '--all',
        action=argparse.BooleanOptionalAction,
        default=False,
        type=bool,
        help='if set - generate all requirements-optional.txt files',
    )

    parser.add_argument(
        '--output-dir',
        default='.',
        type=str,
        help='where the files are generated - default is "."',
    )

    ns = parser.parse_args(args)

    pyproject_path = pathlib.Path(ns.pyproject)
    if not pyproject_path.exists() or not pyproject_path.is_file():
        parser.error(f'cannot find pyproject file {pyproject_path}')
        sys.exit(1)  # this is redundant because parser.error will exit. we keep it here for reasons.

    try:
        with open(pyproject_path, "rb") as fd:
            pyproject = tomllib.load(fd)
    except BaseException:
        parser.error(f"cannot read pyproject.toml file '{pyproject_path}' (odds are the file has syntax errors)")
        raise SystemExit(1)  # again - this is redundant. we keep it here for reasons.

    output_dir = pathlib.Path(ns.output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        parser.error(f"cannot find output directory '{output_dir.absolute()}'")
        sys.exit(1)  # again - this is redundant. we keep it here for reasons.

    project_defs = pyproject.get('project', {})

    exit_code = 0
    if ns.requirements:
        if generate_requirements_files(project_defs, output_dir, ns.requirements) is None:
            exit_code = 1
    else:
        if generate_requirements_files(project_defs, output_dir, ns.all) is None:
            exit_code = 1

    if exit_code != 0:
        parser.error('error: something went wrong...')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
