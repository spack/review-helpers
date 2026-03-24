#!/usr/bin/env spack-python
#
# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
#
# This script automates fetching and checking out the PR branch. The branch
# name will be the PR number to facilitate removal.

import sys

from basics import error
from pull_request import branch
from web import checkout_branch


def usage(args):
    print(f"\nUSAGE: spack-python {args[0]} <spack-PR-#>")
    print("Where:")
    print("  <spack-PR-#> is the number of the PR whose (new) versions are checked")
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        error(f"Invalid arguments: {sys.argv[1:]}")
        usage(sys.argv)

    pr = sys.argv[1]
    branch = branch(pr)
    checkout_branch(pr, branch)
    exit(0)
