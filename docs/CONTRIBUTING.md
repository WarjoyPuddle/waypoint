# Contribution guidelines

## Contents

1. [Introduction](#introduction)
2. [Reporting defects](#reporting-defects)
3. [Proposing improvements](#proposing-improvements)
4. [Submitting pull requests](#submitting-pull-requests)
5. [Development](#development)
    1. [Development on Linux](#development-on-linux)
    2. [The pre-commit hook](#the-pre-commit-hook)

## Introduction

We welcome contributions from the Community, whether they are defect
reports, new feature proposals, or code changes.

To avoid wasted effort, get in touch (e.g. submit an issue) before
making changes.
Sometimes a discussion is required to determine what the best approach
is, or even if a change makes sense in the first place.
In particular, changes that radically alter Waypoint's behaviour, or
which do not align with our long-term vision will not be accepted.

In closing, let us be clear that we evaluate contributions
individually on merit.
In particular, neither your sponsor status nor time served as a
Community member guarantee that a pull request will be merged or an
issue implemented.

## Reporting defects

TODO

## Proposing improvements

TODO

## Submitting pull requests

TODO

## Development

As Waypoint currently has no dependencies, this repository is all you
need for development work.

Use Git for version control.
Do not commit directly to the `main` branch.
Create your own branches instead, one per each feature or bugfix.

Waypoint is a CMake project.
Make sure you have CMake installed to build it.

All source files are encoded using UTF-8.

### Code coverage

Perhaps the most controversial policy enforced in this project's is
the requirement to maintain 100% test coverage in production library
code.
We recognise that this is burdensome and not always possible; we
believe that the benefits are worth the effort.

If you need to exclude a particular piece of code from coverage
metrics, search this repository for the string
`GCOV_COVERAGE_58QuSuUgMN8onvKx` for examples of how to do it using
comments.

So far this policy has presented particular problems in the following
cases:

* **Allocations** The compiler sometimes generates branches for when
the system has enough memory to perform an allocation and for when it
does not.
However, it is difficult to reliably simulate out-of-memory conditions
in tests, leading to uncovered branches.
Consider the following static initialisation (actual production
code snippet at the time of writing).

    ```c++
    auto get_autorun_tests() noexcept -> AutorunManagerTests &
    {
      // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_START
      static AutorunManagerTests tests{
        new AutorunFunctionPtrVector_impl{}};
      // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_STOP

      return tests;
    }
    ```

    We have been unable to test all the branches generated in this code,
    which necessitated the use of exclusion comments (`_BR_` indicates
    that the block is only excluded from branch measurements, not overall
    line coverage).

* **Abnormal program termination** Calls to `std::abort()`,
`std::terminate()`, and termination due to an uncaught exception in
`main()` are some of the reasons that may lead to problems when
gathering coverage metrics.
This is caused by the fact that GCC instruments the program to write
coverage data to disk on program exit using an exit handler;
such handlers are not called during abnormal termination, so some code
may appear uncovered even though it had been executed.
The solution is to have the instrumentation flush its buffers prior
to program termination.
Waypoint provides the function `waypoint::coverage::gcov_dump()`
for this purpose.
This function does nothing in non-coverage builds.

After a coverage build, you will find a helpful coverage report in
`build___/coverage_gcovr_kMkR9SM1S69oCLJ5___/index.html`.

### Development on Linux

On Linux, development is best carried out in a Docker container;
see the files in `infrastructure/docker` for details of the
environment.
To start using the container, make sure you have docker installed and
enabled for `sudo`-less execution.

The `scripts/enter_docker.sh` script will build a Docker image with all the
necessary tooling and start a terminal session inside a container.

While inside the Docker container (or another suitable context), you
can interact with the Waypoint codebase by running the commands in the
`scripts/` directory.

* `clean.sh` removes all build artifacts
* `coverage.sh` builds and runs instrumented tests, outputs coverage report
* `format_code.sh` formats source files
* `short_build.sh` builds Waypoint and functional tests in Debug mode,
runs tests
* `static_analysis.sh` runs static analysis
* `valgrind.sh` builds and runs Valgrind tests
* `verify_build.sh` removes all build artifacts, then builds using all
toolchains, runs all checks and tests, including coverage,
sanitizers, Valgrind, and static analysis).

We recommend working with `short_build.sh` during feature development to
ensure short iterations and quick feedback.
Once the feature is finished, ensure that the `verify_build.sh` build
succeeds and fix any problems if it does not.

### The pre-commit hook

Waypoint comes with a helpful pre-commit hook that will keep you from
falling foul of some of the checks performed during the build.
It is a Python script in `scripts/internal/git_pre_commit_hook.py`;
among other things, it checks if your sources are correctly formatted
and makes sure that you update the notice of copyright in the files
you change.
All you have to do to use it is have Git's pre-commit hook invoke
this script.

A minimal pre-commit hook on Linux would be the following (make sure
the `pre-commit` file is executable).

`.git/hooks/pre-commit`

```shell
#!/bin/sh
python3 "$(pwd)/scripts/internal/git_pre_commit_hook.py"
```
