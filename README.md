# review-helpers

Review-helpers is an *experimental* set of scripts that can be useful for automatically confirming easy-to-check changes in package-related pull requests (PRs).
The scripts here were originally developed when packages were part of the [spack/spack](https://github.com/spack/spack) repository, but evolved to support packages in [spack-packages](https://github.com/spack/spack-packages).


> [!WARNING]
> These checks do *not* represent everything that should be considered during a PR review.
> Refer to the [Package Review Guide](https://spack.readthedocs.io/en/latest/package_review_guide.html) for more information.

> [!NOTE]
> Source: Initial scripts in this repository are snapshots from the original [llnl/spack-tools](https://github.com/llnl/spack-tools) (private) repository.


## Features

This repository provides helpers for checking easy-to-automate aspects of pull request changes involving new and/or updated spack packages.
The focus is on confirming `homepage`s and `version` directives (e.g., branches, commits, tags, and sha256 hashes).

> [!NOTE]
> The original repository precedes the introduction in CI of checksum verification so does not use the same processes.


## Prerequisites

A current installation of [Spack](https://spack.io) **and** this repository are required.


## Setup

The amount of set up required to check a pull request (PR) depends on the nature of the changes.
Simple changes, such as adding new `version` directives, can usually be performed from the `develop` (or equivalent) branch of the package repository.
However, changes to key properties (e.g., `git`, `url` or package equivalent) or a new or modified `url_for_version` method will likely require first checking out the PR.


## Running the scripts

You can run the scripts two ways:

* provide the PR number, or
* provide the name of a package

The first considers changes for **all files in the PR** while the second processes the (locally available) version of the package.

> [!TIP]
> Add the absolute path to this repository's `src` subdirectory to your `PYTHONPATH`.


### Why two options?

Checks of simple additions of `version` directives will likely work using the `develop` branch of the [spack/spack](https://github.com/spack/spack) repository.

> [!WARNING]
> URL-related changes can invalidate the `sha256`s of older `version` directives so you could check out the PR before running the check against the package name.


### New or significantly modified packages

Checking homepages and version directives of PRs that include new packages or significantly modified packages can be done using a single script.

For example, suppose you want to review [spack-packages](https://github.com/spack/spack-packages) PR #1663.
You can run:

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

to get confirmation of new/updated `version` directives and homepages.
We can see that only one of the packages in the PR -- `protobuf` -- has a maintainer.


### New `version` directives only

If the only change involves adding new `version` directives, then you can run the `check_versions.py` script without checking out the PR.
Each package, its maintainers (or contributors in the last year), and the results of the associated version check(s) will be output.

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

The PR only has the `duckdb` package. Its maintainers are `glentner` and `teaguesterling`. And `spack checksum` was used to confirm the `sha256`.

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

shows contributor names and, in parentheses, the numbers of lines each for accounts who have contributed in the last year.
It additionally shows confirmation of the new or updated `version` directives, some as commits, commits+tags, and checksums.

> [!NOTE]
> If you get `Unable to fully confirm` errors, make sure you have the branch checked out.
> If the errors continue, the package is *not* a manual download, and CI checksum verification did not process versions, you could try running `spack checksum` manually.


### New homepage(s) only

If the only changes involve adding or updating homepage property(ies), then you can run the `check_homepages.py` script without checking out the PR.
Each package, its maintainers (or contributors in the last year), and the results of the associated `version` check(s) will be output.

For example, suppose you want to check the homepage change for PR #1840:

```
$ spack-python /path/to/review-helpers/bin/check_homepages.py 1840

babeltrace2 (minghangli-uni):
    confirmed homepage: https://babeltrace.org/
```

Each package, its maintainers (or contributors for the last year), and homepage are reported.
Had the homepage *not* been confirmed the output would have been *unconfirmed homepage*.


### Maintainers only

If the only changes involved adding or updating maintainers, you can run `spack maintainers <package-name>` or use the script.
For example, if you want maintainers for every package in the #1855 PR, you could run:

```
$ spack-python /path/to/review-helpers/bin/check_maints.py 1855
hypre: balay, liruipeng, oseikuffuor1, rfalgout, victorapm, waynemitchell
mfem: acfisher, markcmiller86, tzanio, v-dobrev
palace: cameronrutherford, hughcars, phdum, sbozzolo, simlap

PR #1855: acfisher, balay, cameronrutherford, hughcars, liruipeng, markcmiller86, oseikuffuor1, phdum, rfalgout, sbozzolo, simlap, tzanio, v-dobrev, victorapm, waynemitchell
```

which will list the maintainers for each package and a list of unique maintainers for the PR.


## Limitations

For speed, these scripts typically rely on PR differences and the system you are using.
PRs that customize the version for different platforms -- using dictionaries, for example -- or differences that do not include the `version` part of the directive will not work as expected.
In these cases, you will need to rely on the `CI` check to verify versions or
check out the PR and run a suitable tool (e.g., `spack checksum`).

> [!WARNING]
> None of the available tools will check `version` directives for manually downloaded packages.


## License

This project is part of Spack. Spack is distributed under the terms of both the MIT license and the Apache License (Version 2.0). Users may choose either license, at their option.

All new contributions must be made under both the MIT and Apache-2.0 licenses.

See [LICENSE-MIT](https://github.com/spack/review-helpers/blob/develop/LICENSE-MIT),
[LICENSE-APACHE](https://github.com/spack/review-helpers/blob/develop/LICENSE-APACHE),
[COPYRIGHT](https://github.com/spack/review-helpers/blob/develop/COPYRIGHT), and
[NOTICE](https://github.com/spack/review-helpers/blob/develop/NOTICE) for details.

SPDX-License-Identifier: (Apache-2.0 OR MIT)

LLNL-CODE-811652
