# Lucid C++ unit testing with Waypoint

## Contents

1. [License](#license)
2. [Introduction](#introduction)
3. [Quick start](#quick-start)
    1. [Installation methods](#installation-methods)
        1. [The build-and-install method (recommended)](#the-build-and-install-method-recommended)
        2. [The add_subdirectory method](#the-add_subdirectory-method)
        3. [Providing your own entry point](#providing-your-own-entry-point)
    2. [Writing your first tests](#writing-your-first-tests)
4. [Releases](#releases)
5. [Contributing to Waypoint](#contributing-to-waypoint)
6. [Why "Waypoint"?](#why-waypoint)

## License

Waypoint is available under the MIT license.
For more information, see the [LICENSE](../LICENSE) file in the root directory
of this project.

## Introduction

Waypoint is a minimalistic unit testing framework written in modern C++.
It aims to be stable, intuitive, and quick to master.
Below are some of Waypoint's stand-out features.

* Simple API, only one header
* Only one macro (used for automatic test registration)
* Tests are defined within normal program flow
* Crash resilience (a crashing test does not interfere
  with other tests)
* Uses modern C++23 features internally, but can be adopted even in C++11
  codebases
* Tests are executed in shuffled order by default

## Quick start

### Installation methods

It is easiest to integrate Waypoint into your project if you use
[CMake](https://cmake.org).
You will need to install [Ninja](https://ninja-build.org) to use the
Ninja Multi-Config generator.

Building Waypoint requires a C++23-capable compiler.
It has been confirmed to work out of the box with GCC 15 and Clang 20.
We will use the latter in the examples that follow.

When testing with Waypoint, make sure you do not use variables, classes,
or functions from any namespace named `internal`
(e.g. `waypoint::internal`).
These APIs may not be stable between releases and using them directly
may result in defects up to and including undefined behaviour.
Client-facing APIs are all in the `waypoint` namespace and will remain
stable for the forseeable future.

#### The build-and-install method (recommended)

Start by cloning the Waypoint Git repository and navigate to the
clone's directory.

```shell
git clone ssh://git@github.com/WarjoyPuddle/waypoint.git
cd waypoint
```

To build Waypoint and install the artifacts to a specified location,
execute the following commands.

```shell
cd infrastructure
# Configure step
# You may use -DBUILD_SHARED_LIBS=TRUE if you wish
# to produce a dynamic library.
CC=clang-20 CXX=clang++-20 cmake --preset example_configure -DCMAKE_INSTALL_PREFIX=../build___/waypoint_install___

# Build step
cmake --build --preset example_build --target all --config Debug
cmake --build --preset example_build --target all --config RelWithDebInfo
cmake --build --preset example_build --target all --config Release

# Install step
cmake --build --preset example_build --target install --config Debug
cmake --build --preset example_build --target install --config RelWithDebInfo
cmake --build --preset example_build --target install --config Release
```

If all went well, the directory `build___/waypoint_install___` now
exists.
You are free to rename it if you wish, but for the purposes of this
example, let us keep the name as it is.

In the directory `examples/quick_start_build_and_install` of this
repository, there is a minimal C++ CMake test project which makes use
of the artifacts in `waypoint_install___`.

To build and run the test project, start by copying
`waypoint_install___` into `examples/quick_start_build_and_install`.
In a production scenario, you would probably also add it to your
`.gitignore` file.

```shell
cd examples/quick_start_build_and_install
cp --recursive ../../build___/waypoint_install___ ./

# Configure step
CC=clang-20 CXX=clang++-20 cmake --preset example_configure

# Build step
cmake --build --preset example_build --config Debug

# Run the tests with CMake
cmake --build --preset example_build --target test --config Debug

# Alternatively, run the tests with CTest (a more flexible approach)
ctest --preset example_test --build-config Debug

# You may also run the test executable directly
./build___/Debug/test_program
```

#### The add_subdirectory method

This method uses an approach known as dependency vendoring, where the
client project makes a copy of the dependency's sources and
incorporates them into its own build process.

The directory `examples/quick_start_add_subdirectory` of this
repository contains a minimal C++ CMake test project set up for
vendoring Waypoint.

To build and run the test project, start by copying the
`infrastructure` and `src` directories into
`examples/quick_start_add_subdirectory/third_party___/waypoint`.
In a production scenario, you would probably also track the contents of this
directory using your version control system.
Another approach would be to just clone Waypoint into the
`third_party___/waypoint` directory or use a Git submodule.

```shell
cd examples/quick_start_add_subdirectory
mkdir --parents third_party___/waypoint
cd third_party___/waypoint
cp --recursive ../../../../infrastructure ./
cp --recursive ../../../../src ./
cd ../../

# Configure step
CC=clang-20 CXX=clang++-20 cmake --preset example_configure

# Build step
cmake --build --preset example_build --config Debug

# Run the tests with CMake
cmake --build --preset example_build --target test --config Debug

# Alternatively, run the tests with CTest (a more flexible approach)
ctest --preset example_test --build-config Debug

# You may also run the test executable directly
./build___/Debug/test_program
```

#### Providing your own entry point

If you have special requirements that cannot be satisfied by the
default `main()` function provided by Waypoint, you are free to write
your own.
Apart from compiling it along with your other source files, the only
difference is that you should link against the CMake target
`waypoint::waypoint_no_main` instead of `waypoint::waypoint_main` (which
includes a default entry point).

You will find that this workflow is essentially identical to the
build-and-install method described above.
In particular, you should follow the steps described there to generate
the `waypoint_install___` directory.
Once that is done, you may copy it into the
`examples/quick_start_custom_main` directory, which contains an example
project.
The `main` function is in the file `main.cpp`.

```shell
cd examples/quick_start_custom_main
cp --recursive ../../build___/waypoint_install___ ./

# Configure step
CC=clang-20 CXX=clang++-20 cmake --preset example_configure

# Build step
cmake --build --preset example_build --config Debug

# Run the tests with CMake
cmake --build --preset example_build --target test --config Debug

# Alternatively, run the tests with CTest (a more flexible approach)
ctest --preset example_test --build-config Debug

# You may also run the test executable directly
./build___/Debug/test_program
```

If you wish, it is not difficult to adapt the add_subdirectory workflow
to provide your own program entry point.
Again, the main difference is that you would link against
`waypoint::waypoint_no_main` and not `waypoint::waypoint_main`.

### Writing your first tests

A Waypoint test must belong to a group, identified by its name.
Tests are created with reference to this group, and each test has its own
name as well.
Test names within a group must be unique.

A test's executable body is provided as a callable to its `run()` method.

Assertions are defined through the `Context` parameter passed to the test
body.

The group and test definitions may be wrapped in a `WAYPOINT_AUTORUN` macro,
which ensures automated test registration.

An example `.cpp` file containing Waypoint tests looks like this.
Build it as part of an executable target using CMake and link this target to
the `waypoint::waypoint_main` library, as described in
[Installation methods](#installation-methods).

```c++
WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const add_group = t.group("Addition tests");

  t.test(add_group, "Two plus two equals four")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(2 + 2 == 4);
      });

  t.test(add_group, "One plus three equals four")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(1 + 3 == 4);
      });

  auto const multiply_group = t.group("Multiplication tests");

  t.test(multiply_group, "Two times two equals four")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(2 * 2 == 4);
      });
}
```

For details, in particular those pertaining to test setup, teardown,
and control flow, refer to the [User Guide](USER_GUIDE.md).

## Releases

The Waypoint project follows the Live at Head philosophy.
Every commit undergoes verification to be implicitly releasable and
backwards compatible.
As such, there is no formal feature-driven release schedule and we
encourage consumers to use the latest commit (the "Head") of the `main`
branch.

We will occasionally (e.g. on an annual basis) tag a `main` branch head
commit with a [Semantic Version](https://semver.org) number to mark it
as "supported".
This is in deference to users who require numbered dependency versions,
e.g. due to internal company policies, or who rely on GitHub's Releases
facility.
Tagging also gives us an opportunity to mark milestones, such as the first
feature-complete `1.0.0` version.

If a sufficiently serious defect is discovered in a supported version,
a branch may be created at the supported commit; the fix will be
backported to this branch from `main`.
The commit implementing the fix will be tagged as a patch release.
Supported versions will receive bugfixes for at least two years from
their base supported commit's creation date.

If a client-facing API requires changes that break backwards
compatibility, a deprecation period of at least one year will be
observed prior to removal, unless exceptional circumstances arise
(e.g. a security exploit would unavoidably put users at risk).

## Contributing to Waypoint

Refer to the [contribution guidelines](CONTRIBUTING.md).

## Why "Waypoint"?

A waypoint is a point of reference used for navigation.
The name Waypoint evokes the idea of software development as a journey
towards an end goal.
As we write tests, they serve as waypoints which help us find and
negotiate an optimal route to effective and maintainable software.
