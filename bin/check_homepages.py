#!/usr/bin/env spack-python
#
# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# This script automates the confirmation of homepage(s) for package.py files
# for the provided Pull Request or named package.

import sys

from basics import error
from pull_request import check_homepages


def usage(args):
    print(f"\nUSAGE: spack-python {args[0]} <spack-PR-#|package>")
    print("Where:")
    print("  <spack-PR-#> is the number of the PR whose homepages are checked")
    print("  <package> is the name of the package whose homepage is checked")
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error(f"Invalid arguments: {sys.argv[1:]}")
        usage(sys.argv)

    check_homepages(sys.argv[1])
    exit(0)
