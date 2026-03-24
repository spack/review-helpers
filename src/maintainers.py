# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import json
import re
from typing import List

from basics import debug, error
from pull_request import PullRequest, is_pr, maintainers
from web import web_page

import spack.llnl.util.tty as tty

max_prs = 10

PULL_REQUESTS = "https://api.github.com/repos/spack/spack-packages/pulls"


def get_pr_info(url: str):
    pulls = json.loads(web_page(["-Ls", url]))
    if not pulls:
        return

    if isinstance(pulls, list):
        if not isinstance(pulls[0], dict):
            raise Exception("Cannot create PullRequests from list of non-dict entries")
    elif not isinstance(pulls, dict):
        raise Exception(f"Cannot create PullRequests from {type(pulls)}: {pulls}")

    debug(f"Pull request info: {pulls}")
    return pulls


def pkg_prs(state: str = "open") -> List["PullRequest"]:
    pulls = get_pr_info(PULL_REQUESTS)
    if not pulls:
        return []

    print(f"Processing {len(pulls)} {state} PRs:")
    results = []
    for info in pulls:
        pr = PullRequest(info)
        debug(f"PR: {pr}")
        if pr.state == state:
            results.append(pr)

    return results


def pkg_maintainers(pr: "PullRequest"):
    all_maintainers = []
    if isinstance(pr, PullRequest):
        for pkg in pr.packages:
            accounts = []
            out = maintainers(pkg)
            if out:
                accounts.extend(re.split(", ", out.strip()))
            else:
                accounts.append("None")
            accounts = sorted(set(accounts))
            print(f"{pkg}: {', '.join(accounts)}")

            all_maintainers.extend(accounts)

        if all_maintainers:
            print()
    else:
        error(f"Expected PullRequest: {pr}")
    return sorted(set(all_maintainers))


def check(pr_or_state: str):
    pull_requests = []
    if pr_or_state == "open":
        pull_requests = pkg_prs(pr_or_state)
    elif is_pr(pr_or_state):
        info = get_pr_info(f"{PULL_REQUESTS}/{pr_or_state}")
        if info:
            debug(f"Instantiating PullRequest for PR #{pr_or_state} using {info}")
            pull_requests = [PullRequest(info)]
    else:
        error(f"Cannot check maintainers for {pr_or_state}. Must be a PR or supported state.")

    if tty.is_debug():
        m = len(pull_requests)
        pull_requests = pull_requests[:max_prs]
        n = len(pull_requests)
        debug(f"Processing {n} of {m} pull requests (max {max_prs})")

    for i, pr in enumerate(pull_requests):
        debug(f"Processing {pr.number}")
        maintainers = pkg_maintainers(pr)
        debug(f".. maintainers: {maintainers}")
        if maintainers:
            print(f"PR #{pr.number}: {', '.join(maintainers)}")
