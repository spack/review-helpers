# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# Provide basic web helpers

from basics import debug

from spack.util.executable import which


def checkout_branch(pr, branch):
    # It is far easier to review lots of PRs and those where submitter is
    # using the `develop` branch by naming them locally as the pr number.
    # Then just need to drop the pr number without the pain of copy-and-paste
    # branch names with different special characters.
    if branch == "develop":
        print("\nWARNING: PR is using the 'develop' branch.")

    git = which("git")
    _ = git("fetch", "upstream", f"pull/{pr}/head:{pr}")
    print(f"Fetched {pr}'s {branch} locally as {pr}")
    git("checkout", pr)


def web_page(args):
    curl = which("curl")
    debug(f"Calling curl with args: {args}")

    try:
        options = ["-H", "X-GitHub-Api-Version: 2022-11-28"]
        for opt in options:
            args.insert(-1, opt)
        output = curl(*args, output=str)
    except Exception as e:
        #print(f"curl failed for {args}: {e}")
        #output = ""
        raise

    if "message" in output and "rate limit" in output:
        raise Exception(f"curl failed for {args}: {output}")

    return output
