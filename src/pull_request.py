# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# Provide basic utilities for Spack PR processing.

import collections
import inspect
import json
import os
import re
import sys
from typing import Dict, List

from basics import debug, error, info, warning
import verify
import web

import spack.repo

from spack.cmd.maintainers import packages_to_maintainers
from spack.llnl.util.filesystem import temp_cwd
from spack.main import SpackCommand
from spack.util.executable import which

try:
    from spack.util.string import plural
except:
    from spack.llnl.string import plural

spack_blame = SpackCommand("blame")
spack_checksum = SpackCommand("checksum")
spack_stage = SpackCommand("stage")

git = which("git")

try:
    remotes = git("remote", "-v", output=str)
    spack_repo = "spack-packages" if "spack-packages" in remotes else "spack"
except:
    remotes = None
    spack_repo = "spack"

spack_pr_diff_url = "https://github.com/spack/{0}/pull/{1}.diff"
spack_pr_url = "https://api.github.com/repos/spack/{0}/pulls/{1}"

url_formats = {
    "branch": {"github.com": "{0}//{1}/{2}/{3}/tree/{4}"},
    "branches": {
        "bitbucket.org": "{0}//api.{1}/2.0/repositories/{2}/{3}/branches",
        "github.com": "{0}//api.{1}/repos/REPO/{2}/{3}/branches",
    },
    "commit": {
        "bitbucket.org": "{0}//api.{1}/2.0/repositories/{2}/{3}/commit/{4}",
        "github.com": "{0}//api.{1}/repos/{2}/{3}/commits/{4}",
        "gitlab.com": "{0}//{1}/{2}/{3}/-/commit/{4}",
        "bioconductor.org": "{0}//code.{1}/browse/{3}/commit/{4}",
    },
    "tag": {"github.com": "{0}//{1}/{2}/{3}/releases/tag/{4}"},
    "tags": {
        "bitbucket.org": "{0}//api.{1}/2.0/repositories/{2}/{3}/tags",
        "github.com": "{0}//api.{1}/repos/{2}/{3}/tags",
    },
}

version_args = ["branch", "commit", "sha256", "md5", "tag"]


# Summary processing
homepage_keys = ["unconfirmed", "missing"]
check_keys = version_args + homepage_keys


class PullRequest(object):
    def __init__(self, data: dict):
        if not isinstance(data, dict):
            raise Exception(f"Cannot instantiate PR from ({type(data)}): '{data}'")

        debug("assignees:")
        self.assignees = logins(data.get("assignees", []))
        self.author = data.get("author_association")
        self.diff_url = data.get("diff_url")
        self.number = data.get("number", None)
        debug("packages:")
        self.packages = files(str(self.number), packages=True)
        debug(f".. {self.packages}")
        debug("reviewers:")
        self.reviewers = logins(data.get("requested_reviewers", []))
        debug(f".. {self.reviewers}")
        self.state = data.get("state", None)
        debug("teams:")
        self.teams = logins(data.get("requested_teams", []))
        debug(f".. {self.teams}")
        self.user = data.get("user", {"login": "MISSING"})["login"]

    def __str__(self):
        return f"PullRequest({self.number}, {self.author}, ...)"



def actual_hash(pkg, vers, vers_type):
    try:
        output = spack_checksum(pkg, vers)
    except Exception as e:
        debug(f"Cannot checksum {pkg}@{vers}: {str(e)}")
        return None

    for ln in output.split("\n"):
        vvers, _, data = version(ln)
        if vvers and len(data) == 1:
            entry = data[0]
            if entry.value:
                return entry.value
            elif vers == vvers:
                error(f"Did not detect {entry.type} for {vers} in: {ln}")
            else:
                error(f"Version mismatch: '{vers}' != '{version}'")
    return None


def blame(pkg):
    output = ""
    try:
        data = json.loads(spack_blame("--json", pkg))
        authors = data["authors"]
        submitters = []
        for commit in authors:
            last_commit = commit["last_commit"]
            lines = commit["lines"]
            author = commit["author"]
            if (
                any(
                    [
                        time in last_commit
                        for time in [
                            "day",
                            "days",
                            "week",
                            "weeks",
                            "month",
                            "months",
                            "a year ago",
                        ]
                    ]
                )
                and lines > 1
            ):
                submitters.append(f"{author} ({lines})")
        if len(submitters) > 0:
            # Don't need to highlight source IF provide lines plus providing
            # lines also helps initial assessment of impact of submitter change
            # output = "[blame] " + ", ".join(submitters)
            output = ", ".join(submitters)
    except Exception as e:
        print(f"\nblame ({pkg}): {str(e)}")

    return output


def branch(pr):
    output = git_output(spack_pr_url.format(spack_repo, pr))
    page = json.loads(output)
    if "head" in page:
        return page["head"]["ref"]
    if "message" in page:
        raise Exception(page["message"])
    print(f"Warning: Failed to retrieve branch for {pr}")
    sys.exit(1)


def branch_exists(pkg, branch, git, errors):
    try:
        url = git_url_str(git, branch, "branches")
        if url:
            output = git_output(url)
            if output:
                branches = json.loads(output)
                for _branch in branches:
                    if "name" in _branch and _branch["name"] == branch:
                        return True, url, None

    except Exception as e:
        errors.append(str(e))

    # Can't get through the API so try the branch
    try:
        url = git_url_str(git, branch, "branch")
        if url:
            return check_url_header(url), url

        return False, url

    except Exception as e:
        errors.append(str(e))

    return False, None


def check_homepage_url(ln):
    url = regex_str(r"homepage[ ]*=[ ]*[\"']?([0-9a-zA-Z.:/\-\_]*)", ln)
    if url:
        url = url.strip()
        return check_url_header(url), url

    return False, None


def check_homepages(pr_or_pkg):
    """Process homepages (added to) the PR or exist in the package source."""
    # print_processing(pr_or_pkg)

    if is_pr(pr_or_pkg):
        pkg = None
        # Check the added/modified PR homepage
        output = git_output(spack_pr_diff_url.format("spack-packages", pr_or_pkg))
    else:
        # We're checking the package's homepage regardless
        pkg_cls = package_class(pr_or_pkg)
        if pkg_cls is None:
            return

        output = inspect.getsource(pkg_cls)

    tracker = collections.defaultdict(list)
    output = _compress_lines(output, True)
    pkg_homepages = extract_homepages(pr_or_pkg, output)
    for pkg, conf in pkg_homepages.items():
        print_package(pkg, tracker)

        confirmed, url = conf
        process_homepage(pkg, confirmed, url, tracker)
        print(f"{tracker[pkg][1]}")

    summarize_homepages(len(pkg_homepages), tracker)


def check_pr(pr_or_pkg):
    print_processing(pr_or_pkg)

    tracker = collections.defaultdict(list)
    output, pkg_versions = package_versions(pr_or_pkg)
    pkg_homepages = extract_homepages(pr_or_pkg, output)
    homepage_pkgs = list(pkg_homepages.keys())
    version_pkgs = list(pkg_versions.keys())

    for pkg in sorted(set(homepage_pkgs + version_pkgs)):
        print_package(pkg, tracker)

        # Process the home page first
        if pkg in homepage_pkgs:
            confirmed, url = pkg_homepages[pkg]
            process_homepage(pkg, confirmed, url, tracker)

        # Process versions, which are a dict keyed by version containing
        # (git, [VersionInfo]) tuples
        if pkg in version_pkgs:
            versions = pkg_versions[pkg]
            num = len(versions)
            for vers, (git, data) in versions.items():
                process_pkg_version(pkg, vers, git, data, tracker)
            if num > 1:
                print(f"    {plural(num, 'version')}")

    summarize_packages(tracker)
    summarize_homepages(len(homepage_pkgs), tracker)
    summarize_version_results(pr_or_pkg, pkg_versions, len(version_pkgs), tracker)


def check_source_exists(pkg, vers):
    err = None
    try:
        with temp_cwd():
            spec = f"{pkg}@{vers}"
            output = spack_stage("-p", ".", spec)
            debug(f".. {spec}: {output}")

        return True, None
    except Exception as e:
        err = str(e)

    return False, err


def check_url_header(url):
    output = web.web_page(["-ILs", url])
    if output is None:
        error("Cannot check header when none provided")
        return False

    debug(f"URL header: {output}")

    result = regex_str(r"^HTTP/\d+(?:\.\d+|) ([1-5]\d+)", output.strip())

    # recognize status values as 'confirmation'
    #  200 = OK/Success
    #  301 = moved permanently
    #  302 = temporary redirect
    #  403 = server refuses request (permission|corrupt settings)
    return result in {"200", "301", "302", "403"}


def check_versions(pr_or_pkg):
    print_processing(pr_or_pkg)

    total = 0
    tracker = collections.defaultdict(list)
    _, pkg_versions = package_versions(pr_or_pkg)
    for pkg in pkg_versions:
        print_package(pkg, tracker)

        # Now process relevant version arguments
        num = len(pkg_versions[pkg])
        for vers, (git, data) in pkg_versions[pkg].items():
            process_pkg_version(pkg, vers, git, data, tracker)

        if num > 1:
            print(f"    {plural(num, 'version')}")
        total += num

    summarize_packages(tracker)
    summarize_version_results(pr_or_pkg, pkg_versions, total, tracker)


def commit_exists(pkg, commit, git, errors):
    """Determine if the commit exists in the package's repository."""
    try:
        url = git_url_str(git, commit, "commit")
        if url:
            return check_url_header(url), url

        debug(f"Could not retrieve a URL for {pkg}@{commit}")

    except Exception as e:
        errors.append(str(e))
        error(f"Could not confirm commit due to {str(e)}")

    return False, None


def commits(pr_or_pkg):
    """Return the number of commits in the PR or 0"""
    # Maximum of 250 returned .. not sure if page limited
    # https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-commits-on-a-pull-request
    if not is_pr(pr_or_pkg):
        return 0

    # git_output doesn't seem to work
    output = web.web_page(
        ["-Ls", f"{spack_pr_url.format(spack_repo, pr_or_pkg)}/commits?per_page=250"]
    )
    if output:
        commit_list = json.loads(output)
        return len(commit_list)

    return 0


def contacts(pkg):
    people = maintainers(pkg)
    if len(people) == 0:
        people = blame(pkg)
    return people


def _compress_lines(output, pr=True):
    extra = r"\+" if pr else r""
    regex_subs = [
        # ensure the version is on the same line as its directive
        (r"version\(\n{0}[ ]*".format(extra), r"version("),
        # ensure any added sha256 is on the same line as the previous arg
        (r",\n{0}[ ]*sha256=".format(extra), ", sha256="),
        (r",\n{0}[ ]*\"".format(extra), ', "'),
        (r",\n{0}[ ]*'".format(extra), ", '"),
        (r",\n{0}[ ]*submodules=".format(extra), ", submodules='"),
        # ensure any added branch is on the same line as the previous argument
        (r",\n{0}[ ]*branch=".format(extra), ", branch="),
        # ensure any added commit is on the same line as the previous argument
        (r",\n{0}[ ]*commit=".format(extra), ", commit="),
        # ensure any added git is on the same line as the previous argument
        (r",\n{0}[ ]*git=".format(extra), ", git="),
        # ensure any added extension is on same line as the previous argument
        (r",\n{0}[ ]*extension=".format(extra), ", extension="),
        # ensure any preferred arg is on the same line as the previous arg
        (r",\n{0}[ ]*preferred=".format(extra), ", preferred="),
        # ensure any deprecated arg is on the same line as the previous arg
        (r",\n{0}[ ]*deprecated=".format(extra), ", deprecated="),
        # ensure any added tag is on the same line as the previous argument
        (r",\n{0}[ ]*tag=".format(extra), ", tag="),
        # ensure any added url is on the same line as the previous argument
        (r",\n{0}[ ]*url=".format(extra), ", url="),
        # ensure homepage is on the same line as the previous argument
        (r"{0}[ ]*homepage[ ]*=[ ]*[\(]?[\n]?".format(extra), " homepage ="),
        # ensure drop open braces after equals
        (r"=\+", "="),
    ]

    for regex, sub in regex_subs:
        output = re.sub(regex, sub, output)

    return output


def extract_homepages(pr_or_pkg, output):
    homepages = {}
    pkg = None
    pr = is_pr(pr_or_pkg)
    url = None
    output = _compress_lines(output, pr=False)
    for ln in output.split("\n"):
        if pr and ln.startswith("+++") and ln.endswith("package.py"):
            pkg = os.path.basename(os.path.dirname(ln.split()[1]))
            continue
        elif "homepage" not in ln:
            continue

        pkg = pkg or pr_or_pkg
        ln = ln[1:] if pr else ln
        confirmed, url = check_homepage_url(ln)
        if pkg not in homepages:
            homepages[pkg] = (confirmed, url)
        elif confirmed and url:
            homepages[pkg] = (confirmed, url)

    return homepages


def _add_valid_version(pkg, ln, new_versions):
    vers, git, data = version(ln[1:])
    pre = f"{pkg}: {vers}:"
    if vers is None or vers == "self":
        return

    if data is None:
        debug(f"{pre} no info extracted from {ln}")
        return

    debug(f"{pre} extracted {vers}, {git}, {data}")

    match = 0
    for entry in data:
        if entry.type in version_args:
            match += 1

    if match != len(data):
        info(f"{pre} Did not detect supported arguments: {version_args}")
        return

    debug(f"{pre} Processing version {vers}")
    new_versions[pkg][vers] = (git, data)


def extract_pkg_versions(pkg, source):
    """Extract all of a package's specified versions.

    Returns:
        dict: versions keyed by package containing dict keyed by versions
              and containing (git, [VersionInfo]) tuples.
    """
    debug(f"Extracting {pkg} versions from source")

    new_versions = collections.defaultdict(dict)
    source = _compress_lines(source, pr=False)
    output = source.split("\n")
    for ln in output:
        _add_valid_version(pkg, ln, new_versions)
    return new_versions


def extract_pr_versions(pr, output):
    """Extract versions that are *added* to the PR.

    Warning: This does mean that changes where the directive ("version(")
    line is unchanged will NOT be detected as new versions.
    """
    debug(f"extracting {pr} versions from diffs:\n{output}")
    output = _compress_lines(output, pr=True)
    new_versions = collections.defaultdict(dict)
    pkg = None
    for ln in output.split("\n"):
        if ln.startswith("+++") and ln.endswith("package.py"):
            pkg = os.path.basename(os.path.dirname(ln.split()[1]))
        elif ln.startswith("+"):
            _add_valid_version(pkg, ln, new_versions)

    return new_versions


def files(pr_or_pkg, packages=True):
    """Return the list of file names for a pull request"""
    # Maximum of 3000 returned, but 30 per page by default so set page to 250(?)
    # https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files
    if not is_pr(pr_or_pkg):
        return [pr_or_pkg]

    # NOTE: git_output doesn't work if pass formatted URL
    debug(f"Extracting files for {pr_or_pkg}")
    output = web.web_page(
        ["-Ls", f"{spack_pr_url.format(spack_repo, pr_or_pkg)}/files?per_page=250"]
    )
    if output:
        files_list = json.loads(output)
        names = []
        for data in files_list:
            assert isinstance(data, dict), f"Expected dict, not {type(data)}"
            filename = data["filename"]
            basename = os.path.basename(filename)
            if packages and basename != "package.py":
                continue

            names.append(os.path.basename(os.path.dirname(str(filename))) if packages else filename)
        return names

    return []


def git_output(url):
    debug(f"retrieving {url}")
    output = web.web_page(["-Ls", url])
    return output


def git_url_str(git, value, url_type):
    debug(f"git_url_str: called with {git}, {value}, {url_type}")

    if not (git and url_type):
        error(f"Git is required to determine the api {url_type} url")
        return None

    if not isinstance(git, str):
        return None

    if "git.bioconductor" in git:
        git = git.replace("git.", "")

    segments = git.split("/")
    formats = url_formats[url_type]
    debug(f"git_url_str: {git}: {segments}, {formats}")

    for site in formats:
        if site in git:
            fmt = formats[site]
            args = [
                segments[0],  # protocol
                site,  # repository site
                segments[3],  # owner
                segments[4].replace(".git", ""),  # repository
                value,  # version value (e.g. commit)
            ]
            url = fmt.format(*args)
            debug(f"git_url_str: {args}: {url}")

            return url

    return git.replace(".git", "")


def is_pr(pr_or_pkg):
    debug(f"Checking if '{pr_or_pkg}' ({type(pr_or_pkg)}) is a PR")
    return pr_or_pkg.isdigit()


def logins(accounts: Dict) -> List[str]:
    debug(f"Extracting github accounts from {accounts}")
    if not accounts:
        return []

    debug(f".. processing {accounts}")
    return [a.get("login", "NONE") for a in accounts]


def maintainers(pkg):
    try:
        pkg_to_users = packages_to_maintainers([pkg])
        output = ", ".join(sorted(set(pkg_to_users[pkg])))
    except Exception as e:
        output = ""
        print(f"maintainers ({pkg}): {str(e)}")

    return output


def package_class(pr_or_pkg):
    try:
        pkg_cls = spack.repo.path.get_pkg_class(pr_or_pkg)
    except AttributeError:
        try:
            pkg_cls = spack.repo.PATH.get_pkg_class(pr_or_pkg)
        except spack.repo.UnknownPackageError as err:
            error(f"{pr_or_pkg}: running from {os.getcwd()}")
            warning(f"Skipping {pr_or_pkg}: {str(err)}")
            return None
    return pkg_cls


def package_versions(pr_or_pkg):
    """Extract source code and package version information"""
    # Check the added/modified PR versions
    if is_pr(pr_or_pkg):
        output = git_output(spack_pr_diff_url.format(spack_repo, pr_or_pkg))
        return output, extract_pr_versions(pr_or_pkg, output)

    # We're checking all of a package's specified versions
    pkg_cls = package_class(pr_or_pkg)
    if pkg_cls is None:
        return

    source = inspect.getsource(pkg_cls)
    return source, extract_pkg_versions(pkg_cls.name, source)


def print_package(pkg, tracker):
    people = contacts(pkg)
    tracker[pkg].append(people)
    print(f"\n{pkg} ({people}):")


def print_processing(pr_or_pkg):
    pr = is_pr(pr_or_pkg)
    checking = " PR #" if pr else " "
    print(f"\nProcessing{checking}{pr_or_pkg}")


def process_homepage(pkg, confirmed, url, tracker):
    if url:
        if confirmed:
            pre = ""
        else:
            pre = "un"
            tracker["unconfirmed"].append(pkg)
        status = f"  {pre}confirmed homepage: {url}"
    else:
        status = "  homepage url is missing"
        tracker["missing"].append(pkg)

    tracker[pkg].append(status)


def process_pkg_version(pkg, vers, git, data, tracker):
    if vers == "self" or len(data) < 1:
        return

    if data is None:
        result = f"  version {vers}:  unconfirmed (Okay if a bundle package)"
        tracker[pkg].append(result)
        print(result)
        return

    if git is None:
        pkg_cls = package_class(pkg)
        if pkg_cls is None:
            result = f"  version {vers}:  unconfirmed (no package class for extracting git url)"
            tracker[pkg].append(result)
            print(result)
            return

        git = pkg_cls.git if pkg_cls and hasattr(pkg_cls, "git") else None

    status = []
    successes = 0
    for entry in data:
        if entry.type in ["md5", "sha256"]:
            vhash = actual_hash(pkg, vers, entry.type)
            if vhash:
                if vhash == entry.value:
                    status.append(f"confirmed {entry.type} (checksum)")
                    successes += 1
                else:
                    status.append(f"expected {entry.value}, actual {vhash}")
            else:
                status.append(f"expected {entry.value}, actual {vhash}")
                tracker[entry.type].append(f"spack checksum {pkg} {vers}")
            # Assuming no tags, etc. with hashes
            break

        elif entry.type in ["branch", "commit", "tag"]:
            errors = []
            checker = version_checker[entry.type]
            debug(f"Using {checker.__name__} to check {pkg} using {git}")

            exists, url = checker(pkg, entry.value, git, errors)
            if exists:
                # status.append(f"{checker.__name__} confirmed {entry.type}")
                status.append(f"confirmed {entry.type}")
                successes += 1
            else:
                # The simpler, faster APIs don't seem to work, try
                # fetching instead.
                error(f"{checker.__name__} could not confirm {entry.type}\n")
                exists, err = check_source_exists(pkg, vers)
                if exists:
                    status.append(f"confirmed {entry.type} (fetcher)")
                    successes += 1
                else:
                    spec = f"{pkg}@{vers}"
                    if debug:
                        if err:
                            errors.append(err)
                        errs = "\n".join(errors)
                        error(f"Could not confirm {spec}: {errs}")

                    url_str = f" using {url}" if url else ""
                    status.append(f"could not confirm {entry.type} for {spec}{url_str}: {err}")
                    tracker[entry.type].append(f"spack fetch {pkg}@{vers}")
        else:
            status.append(f"Unrecognized {entry.type} version")

    if len(data) != successes:
        status.append(f"Unable to fully confirm version for {pkg}@{vers}")

    status_lines = "\n\t\t\t".join(status)
    result = f"  version {vers}:  {status_lines}"
    tracker[pkg].append(result)
    print(result)


def regex_str(regex, ln):
    match = re.search(regex, ln)
    if match:
        return match.group(1)


def summarize_homepages(total, tracker):
    if total > 1:
        print(f"\nProcessed {plural(total, 'homepage package')}")
    elif total == 0:
        print("\nNo homepage changes were detected.")

    for key in homepage_keys:
        pkgs = tracker[key]
        if pkgs:
            print(
                f"\n{key.capitalize()} {plural(len(pkgs), 'package')}: {', '.join(pkgs)}"
            )

    if tracker["missing"]:
        print(f"\nMissing homepage(s) in: {', '.join(tracker['missing'])}")


def summarize_packages(tracker):
    print("\nPackage Summary:")
    for key, data in tracker.items():
        if key not in check_keys:
            print(f"\n  {key} ({data[0]}):")
            for res in data[1:]:
                print(f"    {res}")


def summarize_version_results(pr_or_pkg, pkg_versions, total, tracker):
    if total > 1:
        print(
            "\nProcessed {0}, {1}".format(
                plural(len(pkg_versions), "version package"), plural(total, "version")
            )
        )
    elif total == 0:
        extra = {True: "\n\nHint: Is the directive included in the change?", False: ""}
        print(f"\nNo version changes were detected.{extra[is_pr(pr_or_pkg)]}")
        return

    for commands, desc in [
        (tracker["sha256"], "checksum"),
        (tracker["branch"], "fetch"),  # "check repository for branches"),
        (tracker["commit"], "fetch"),
        (tracker["tag"], "fetch"),  # "check repository for tags"),
    ]:
        if commands:
            print(f"\nMust manually {desc}:")
            for cmd in commands:
                print(cmd)


def tag_exists(pkg, tag, git, errors):
    """Determine if the tag exists in the package repository."""
    try:
        # Try the tags API since currently have URLs for multiple sites
        url = git_url_str(git, tag, "tags")
        if url:
            output = git_output(url)
            if output:
                tags = json.loads(output)
                for _tag in tags:
                    if "name" in _tag and _tag["name"] == tag:
                        return True, url

    except Exception as e:
        errors.append(str(e))

    # Can't get through the API so try to get the release tag.
    #
    # This can happen if the tag does not appear in the limited number
    # of returned tags.
    try:
        url = git_url_str(git, tag, "tag")
        if url:
            return check_url_header(url), url

        return False, url

    except Exception as e:
        errors.append(str(e))

    return False, None


class VersionInfo:
    def __init__(self, value, vtype):
        self.value = value
        self.type = vtype

    def __str__(self):
        return f"({self.value}, {self.type})"

    def __repr__(self):
        return f"({self.value}, {self.type})"


def version(ln):
    # Returns vers, git | None, List[VersionInfo] | None
    vers = regex_str(r"version\([\"']?([\w.-]+)", ln)
    if not vers:
        debug(f"no version detected in {ln}")
        return None, None, None

    data = []
    possible_sha = regex_str(r", [\"']([0-9a-f]*)[\"']", ln)
    if possible_sha:
        return vers, None, [VersionInfo(possible_sha, "sha256")]

    git = regex_str(r"git=[\"']?([0-9a-zA-Z.:/\-\_]*)", ln)
    if git:
        debug(f"Found git={git} in {ln}")

    sha = regex_str(r"sha256=[\"']?([0-9a-f]*)", ln)
    if sha:
        debug(f"detected sha256: {sha}")
        data.append(VersionInfo(sha, "sha256"))

    branch = regex_str(r"branch=[\"']?([0-9a-zA-Z.\-]*)", ln)
    if branch:
        debug(f"detected branch: {branch}")
        data.append(VersionInfo(branch, "branch"))

    commit = regex_str(r"commit=[\"']?([0-9a-f]*)", ln)
    if commit:
        debug(f"detected commit: {commit}")
        data.append(VersionInfo(commit, "commit"))

    tag = regex_str(r"tag=[\"']?([0-9a-zA-Z.\-]*)", ln)
    if tag:
        debug(f"detected tag: {tag}")
        data.append(VersionInfo(tag, "tag"))

    if len(data) > 0:
        return vers, git, data

    md5 = regex_str(r"md5=[\"']?([0-9a-f]*)", ln)
    if md5:
        debug(f"detected md5: {md5}")
        return vers, git, [VersionInfo(md5, "md5")]

    return vers, None, None


# Note the following needs to appear *after* the definition of the last checker
version_checker = {"branch": branch_exists, "commit": commit_exists, "tag": tag_exists}
