#!/usr/bin/env spack-python
#
# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# This script automates checking aspects of package.py file(s) that are part
# of the specified pull request or a package.

import sys

from basics import error
from pull_request import check_pr


def usage(args):
    print(f"\nUSAGE: spack-python {args[0]} <spack-PR-#|package>")
    print("Where:")
    print("  <spack-PR-#> is the number of the PR whose packages are checked")
    print("  <package> is the name of the package to check")
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error(f"Invalid arguments: {sys.argv[1:]}")
        usage(sys.argv)

    check_pr(sys.argv[1])
    exit(0)
