#!/usr/bin/env spack-python
#
# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# This script automates checking version directives in package.py file(s) in
# a Pull Request (PR) or named package.

import sys

from basics import error
from pull_request import check_versions


def usage(args):
    print(f"\nUSAGE: spack-python {args[0]} <spack-PR-#|package>")
    print("Where:")
    print("  <spack-PR-#> is the number of the PR whose (new) versions are checked")
    print("  <package> is the name of the package whose versions are checked")
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        error("requires at least one PR or package")
        usage(sys.argv)

    for p in sys.argv[1:]:
        check_versions(p)
    exit(0)
