#!/usr/bin/env spack-python
#
# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# This script supports listing maintainers for all packages in a Pull Request
# (PR), all open package PRs, or a named package.

import sys

from basics import error
from maintainers import check

import spack.llnl.util.tty as tty


# enable/disable debugging
#tty.set_debug(1)

# enable/disable stacktraces
#tty.set_stacktrace(True)


def usage(args):
    print(f"\nUSAGE: spack-python {args[0]} <spack-PR-#|<package>|open>")
    print("Where:")
    print("  <spack-PR-#> is the number of the PR whose maintainers are checked")
    print("  <package>    is the name of the package whose maintainers is checked")
    print("  open         means to check maintainers for all open package PRs")
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error(f"Invalid arguments: {sys.argv[1:]}")
        usage(sys.argv)

    check(sys.argv[1])
    exit(0)
