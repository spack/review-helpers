# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# Common, basic features

import re
from typing import List, Tuple

import spack.error
import spack.llnl.util.tty as tty

debug = True

spack.error.debug = debug
#spack.error.SHOW_BACKTRACE = debug

BUILTIN = re.compile(r"repos\/builtin\/packages\/([^\/]+)\/package\.py")


def debug(msg):
    tty.debug(msg)


def error(msg):
    tty.error(msg)


def info(msg):
    tty.info(msg)


def warning(msg):
    tty.warn(msg)


def pkgs(files: List[str]) -> List[Tuple[str, str]]:
    return [(m.group(1), p) for p in files for m in [BUILTIN.search(p)] if m]
