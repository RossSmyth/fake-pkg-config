import itertools
import sys
from collections.abc import Iterator
from typing import Dict, List

from args import get_parser
from libs import Lib
from pkg_config import BasePkgConfig, FakePkgConfig, RealPkgConfig


def main() -> None:
    arg_parser = get_parser()

    args, _ = arg_parser.parse_known_args(sys.argv)

    real_pkg_config = RealPkgConfig()
    fake_pkg_config = FakePkgConfig()

    libs_to_pkg: dict[Lib, BasePkgConfig] = dict()

    # Assign a mapping so we don't have to check each time what
    # pkg-config to use
    if real_pkg_config.pkg_config is not None:
        for lib in args.libs:
            if real_pkg_config.exists(lib):
                libs_to_pkg[lib] = fake_pkg_config
            else:
                libs_to_pkg[lib] = real_pkg_config
    else:
        libs_to_pkg.fromkeys(args.libs, fake_pkg_config)

    # pkg-config silently ignore duplicated args
    flags = list(dict.fromkeys(args.arg_queue))

    # The vars pass in via CLI, in order
    vars: list[str] = list(args.variable)

    # Iterator of the output. Will be joined with ' '
    output: Iterator[str] = iter([])

    for flag in flags:
        match flag:
            case "libs":
                output = itertools.chain(
                    output,
                    (val[1].get_libs(val[0]) for val in libs_to_pkg.items()),
                )
            case "cflags":
                output = itertools.chain(
                    output,
                    (val[1].get_cflags(val[0]) for val in libs_to_pkg.items()),
                )
            case "modversion":
                output = itertools.chain(
                    output,
                    (val[1].get_modversion(val[0]) for val in libs_to_pkg.items()),
                )
            case "variable":
                output = itertools.chain(
                    output,
                    (
                        val[1].get_variable(val[0], vars.pop(0))
                        for val in libs_to_pkg.items()
                    ),
                )
            case other:
                raise ValueError(f"Unknown flag {other}")

    # Unpack the iter to stdout
    print(*output, end="", sep=" ")
