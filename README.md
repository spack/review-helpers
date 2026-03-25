# review-helpers

Review-helpers is an *experimental* set of scripts that can be useful for automatically confirming easy-to-check changes in package-related pull requests (PRs).

The scripts can be used to confirm:

* `homepage` URL resolves to a valid, accessible site;
* `version` directive arguments (e.g., `sha256`, `branch`, `tag`, `commit`) match what is in the repository; and
* all listed `maintainers` for the packages are notified either by being listed under `Reviewers` or added in a PR comment.

Due to restrictions, not all accounts listed in the `maintainers` directives of the modified packages will necessarily make it to the GitHub `Reviewers` list.
So compiling this information for a PR can help should you want to notify the missing  maintainers that there has been a change to one or more of their packages.

> [!WARNING]
> These checks do *not* represent everything that should be considered during a PR review.
> Refer to the [Package Review Guide](https://spack.readthedocs.io/en/latest/package_review_guide.html) for more information.

> [!NOTE]
> The scripts here were originally developed when packages were part of the [spack/spack](https://github.com/spack/spack) repository, but evolved to support packages in [spack-packages](https://github.com/spack/spack-packages).
> They are snapshots of the files from the original [llnl/spack-tools](https://github.com/llnl/spack-tools) (private) repository.


## Features

This repository provides helpers for checking easy-to-automate aspects of pull request changes involving new and/or updated spack packages.
The focus is on confirming `homepage`s and `version` directives (e.g., branches, commits, tags, and sha256 hashes) and identifying maintainers.
Knowing the maintainers for affected packages can be helpful in determining the extent to which a PR needs additional reviews.
For example, a PR submitted from someone who is not a maintainer of the packages will likely need additional reviews from the maintainer.
There is more information on this in the [Package Review Guide](https://spack.readthedocs.io/en/latest/package_review_guide.html).

> [!WARNING]
> The original repository precedes the introduction in CI of checksum verification so does not use the same processes.
> This feature can be leveraged to more easily check older version directives and as an aid to debugging URL-related changes.


## Prerequisites

A current installation of [Spack](https://spack.io) **and** this repository are required.


## Setup

The amount of set up required to check a pull request (PR) depends on the nature of the changes.

*At a minimum* you will need to set up the Spack environment by sourcing the appropriate [setup-env shell script](https://spack.readthedocs.io/en/latest/getting_started.html) **and** add the absolute path to `PYTHONPATH` for the `src` subdirectory here.
You will also want to be in your `spack/spack-packages` clone when you run the scripts.

Beyond that, you'll want to check out the appropriate branch depending on the PR.
Simple changes, such as just adding new `version` directives, can usually be performed from the `develop` (or equivalent) branch of the package repository.
However, changes to key properties (e.g., `git`, `url`) or a new or modified `url_for_version` method will likely require first checking out the PR.
The same goes for changes to implicit, or derived, `url`s such as `PythonPackage`'s [pypi property](https://spack.readthedocs.io/en/latest/build_systems/pythonpackage.html#).


## Running the scripts

You can run the scripts two ways:

* provide the PR number, or
* provide the name of a package

The first considers changes for **all files in the PR** while the second processes the (locally available) version of the package.


### Why two options?

Checks of simple additions of `version` directives will likely work using the `develop` branch of the [spack/spack](https://github.com/spack/spack) repository.
However, URL-related changes can invalidate the `sha256`s of older `version` directives so you might need to check out the PR first.
In which case, you could run the following to check out PR #1234:

```
$ spack-python /path/to/review-helpers/bin/fetch_pr_branch.py 1234
```

The local branch name will be `1234`.

The PR number is used for the local branch name to help reviewers who also contribute to Spack distinguished from their personal branches.
This makes identify review branches for removal (using `git branch -D <PR-number>`) a *lot* easier.


### New or significantly modified packages

Checking `homepage`s and `version` directives of PRs that include new or significantly modified packages can be done using a single script.

For example, suppose you want to review [spack-packages](https://github.com/spack/spack-packages) PR #1663.
While under the clone's root, you can run:

```
$ spack-python /path/to/review-helpers/bin/check_versions.py 1663

Processing PR #1663

... Omitting progress reporting ...

Package Summary:

  protobuf (hyoklee):
      version 32.1:  confirmed sha256 (checksum)

  py_binary (Adam J. Stewart (13)):
      confirmed homepage: https://github.com/ofek/binary
      version 1.0.2:  confirmed sha256 (checksum)

  py_google_cloud_bigquery (Adam J. Stewart (17)):
      confirmed homepage: https://github.com/googleapis/python-bigquery
      version 3.38.0:  confirmed sha256 (checksum)

  py_google_cloud_core (Adam J. Stewart (11)):
      version 2.4.1:  confirmed sha256 (checksum)

  py_grpcio (Adam J. Stewart (68), Harmen Stoppels (5), Teague Sterling (6)):
      version 1.75.0:  confirmed sha256 (checksum)

  py_grpcio_status (Adam J. Stewart (13), Teague Sterling (5)):
      confirmed homepage: https://grpc.io/
      version 1.75.0:  confirmed sha256 (checksum)

  py_protobuf (Adam J. Stewart (30), Teague Sterling (2)):
      confirmed homepage: https://developers.google.com/protocol-buffers/
      version 6.32.1:  confirmed sha256 (checksum)

  py_pypinfo (Adam J. Stewart (17)):
      confirmed homepage: https://github.com/ofek/pypinfo
      version 22.0.0:  confirmed sha256 (checksum)

  py_tinyrecord (Adam J. Stewart (9)):
      confirmed homepage: https://github.com/eugene-eeo/tinyrecord
      version 0.2.0:  confirmed sha256 (checksum)

Processed 6 homepage packages

Processed 9 version packages, 9 versions
```

> [!NOTE]
> The appearance of `(checksum)` means the version's `sha256` was confirmed using `spack checksum`.

> [!TIP]
> **What am I looking for here?**
> I make sure the `version` directives and `homepage`s are `confirmed`; the homepage (ideally) uses `https`; and, if there are maintainers, that they either appear under `Reviewers` in the PR or have been "notified" in a comment.


### New `version` directives only

If the only change involves adding new `version` directives, then you can generally run the `check_versions.py` script without checking out the PR.
The exception is if a `url` argument is provided in a `version` directive.
Each package, its maintainers (or contributors in the last year), and the results of the associated version checks will be output.

For example, suppose you want to review [spack-packages](https://github.com/spack/spack-packages) PR #3958.
You can run:

```
$ spack-python /path/to/review-helpers/bin/check_versions.py 3906

Processing PR #3958

duckdb (glentner, teaguesterling):
  version 1.5.1:  confirmed sha256 (checksum)

Package Summary:

  duckdb (glentner, teaguesterling):
      version 1.5.1:  confirmed sha256 (checksum)
```

The PR only has the `duckdb` package. Its maintainers are `glentner` and `teaguesterling`. And, since `(checksum)` is shown, `spack checksum` was used to confirm the `sha256`.

If the package didn't have maintainers, the output would show a list of GitHub accounts that have contributed to the package in the last year.
For example,

```
$ spack-python /path/to/review-helpers/bin/check_versions.py 3906

Processing PR #3906

... omitting redundant output since a single package ...

Package Summary:

  samrai (Lina Muryanto (163), Harmen Stoppels (2), Adam J. Stewart (3), Massimiliano Culpo (3)):
      version 4.5.0:  confirmed commit
			confirmed tag
      version 4.3.0:  confirmed commit
			confirmed tag
      version 2022.2.9:  confirmed commit
      version 2021.11.4:  confirmed commit
      version 2021.2.16:  confirmed commit
      version 3.12.0:  confirmed sha256 (checksum)
      version 3.11.5:  confirmed sha256 (checksum)
      version 3.11.4:  confirmed sha256 (checksum)
      version 3.11.2:  confirmed sha256 (checksum)
      version 3.11.1:  confirmed sha256 (checksum)
      version 3.10.0:  confirmed sha256 (checksum)
      version 3.9.1:  confirmed sha256 (checksum)
      version 3.8.0:  confirmed sha256 (checksum)
      version 3.7.3:  confirmed sha256 (checksum)
      version 3.7.2:  confirmed sha256 (checksum)
      version 2.4.4:  confirmed sha256 (checksum)

Processed 1 version package, 16 versions
```

shows contributor names instead of maintainers and, in parentheses, the maximum number of lines contributed in the last year.

The reason for showing the maximum numbers of lines contributed is to give a rough indication of their interest in the package, where a few lines could represent the addition of a new `version` directive.
This information was relevant when, in the absence of package maintainers, we suggested people run `spack blame` to find others who may still care about the package.

> [!NOTE]
> If you get `Unable to fully confirm` errors, make sure you have the branch checked out.
> If the errors continue, the package may be a manual download.
> Review the CI checksum verification check to see if it processed the versions.
> You could also run `spack checksum` manually.

> [!TIP]
> **What am I looking for here?**
> I make sure the version directives are `confirmed` and, if there are maintainers, that they either appear under `Reviewers` in the PR or have been "notified" in a comment.


### New homepages only

If the only changes involve adding or updating `homepage` property(ies), then you can run the `check_homepages.py` script without checking out the PR.
Each package, its maintainers (or contributors in the last year), and the results of checking for the existence of the homepages will be output.

For example, suppose you want to check homepage changes for PR #1840:

```
$ spack-python /path/to/review-helpers/bin/check_homepages.py 1840

babeltrace2 (minghangli-uni):
    confirmed homepage: https://babeltrace.org/
```

> [!NOTE]
> If the homepage *cannot* been confirmed the output would show as *unconfirmed*.

> [!TIP]
> **What am I looking for here?**
> I make sure the homepage is `confirmed` and, if there are maintainers, that they either appear under `Reviewers` in the PR or have been "notified" in a comment.


### Maintainers only

If the only changes involved adding or updating maintainers, you can run `spack maintainers <package-name>` or use the script.

For example, if you want a unique list of maintainers for every package in a multi-package PR, like #1855, you could run:

```
$ spack-python /path/to/review-helpers/bin/check_maints.py 1855
hypre: balay, liruipeng, oseikuffuor1, rfalgout, victorapm, waynemitchell
mfem: acfisher, markcmiller86, tzanio, v-dobrev
palace: cameronrutherford, hughcars, phdum, sbozzolo, simlap

PR #1855: acfisher, balay, cameronrutherford, hughcars, liruipeng, markcmiller86, oseikuffuor1, phdum, rfalgout, sbozzolo, simlap, tzanio, v-dobrev, victorapm, waynemitchell
```

> [!TIP]
> **What am I looking for here?**
> I tend to only use this feature if there are a LOT of packages and I want to know 1) if there is a maintainer to review each package and 2) there is a unique list of maintainers so I can make sure that each either appears under `Reviewers` in the PR or have been "notified" in a comment.


## Limitations

For speed, these scripts typically rely on PR differences and the system you are using.
PRs that customize the version for different platforms -- using dictionaries, for example -- or differences that do not include the `version` part of the directive will not work as expected.
In these cases, you will need to rely on the `CI` check to verify versions or
check out the PR and run a suitable tool (e.g., `spack checksum`).

> [!WARNING]
> None of the currently available tools will check `version` directives for manually downloaded packages.


## License

This project is part of Spack. Spack is distributed under the terms of both the MIT license and the Apache License (Version 2.0). Users may choose either license, at their option.

All new contributions must be made under both the MIT and Apache-2.0 licenses.

See [LICENSE-MIT](https://github.com/spack/review-helpers/blob/develop/LICENSE-MIT),
[LICENSE-APACHE](https://github.com/spack/review-helpers/blob/develop/LICENSE-APACHE),
[COPYRIGHT](https://github.com/spack/review-helpers/blob/develop/COPYRIGHT), and
[NOTICE](https://github.com/spack/review-helpers/blob/develop/NOTICE) for details.

SPDX-License-Identifier: (Apache-2.0 OR MIT)

LLNL-CODE-811652
