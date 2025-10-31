# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import argparse
import contextlib
import dataclasses
import datetime
import enum
import hashlib
import json
import multiprocessing
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import typing

PYTHON = (
    "python3" if (sys.executable is None or sys.executable == "") else sys.executable
)

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/..")

COVERAGE_DIR_LCOV = os.path.realpath(
    f"{PROJECT_ROOT_DIR}/coverage_lcov_3XxYQrYbuY5AnPYH___"
)
COVERAGE_FILE_LCOV = os.path.realpath(f"{COVERAGE_DIR_LCOV}/coverage.info")
COVERAGE_DIR_GCOVR = os.path.realpath(
    f"{PROJECT_ROOT_DIR}/coverage_gcovr_kMkR9SM1S69oCLJ5___"
)
COVERAGE_FILE_HTML_GCOVR = os.path.realpath(f"{COVERAGE_DIR_GCOVR}/index.html")
COVERAGE_FILE_JSON_GCOVR = os.path.realpath(f"{COVERAGE_DIR_GCOVR}/coverage.json")
INFRASTRUCTURE_DIR = os.path.realpath(f"{PROJECT_ROOT_DIR}/infrastructure")
CMAKE_SOURCE_DIR = INFRASTRUCTURE_DIR
CMAKE_LISTS_FILE = os.path.realpath(f"{CMAKE_SOURCE_DIR}/CMakeLists.txt")
CMAKE_PRESETS_FILE = os.path.realpath(f"{CMAKE_SOURCE_DIR}/CMakePresets.json")
assert os.path.isfile(CMAKE_LISTS_FILE) and os.path.isfile(CMAKE_PRESETS_FILE)

MAIN_HEADER_PATH = f"{PROJECT_ROOT_DIR}/src/waypoint/include/waypoint/waypoint.hpp"
assert os.path.isfile(MAIN_HEADER_PATH), "waypoint.hpp does not exist"

INSTALL_TESTS_DIR_PATH = os.path.realpath(f"{PROJECT_ROOT_DIR}/test/install_tests")
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR = os.path.realpath(
    f"{INSTALL_TESTS_DIR_PATH}/find_package_no_version_test"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR}/waypoint_install_linux_clang_MItqq12bE9VvgzWH___"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR}/waypoint_install_linux_gcc_99V4LexZ8aO7qhLC___"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR}/waypoint_install_linux_clang_shared_CJGWSsRXagJ22vHV___"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR}/waypoint_install_linux_gcc_shared_JRXQmCKTnzVcAYbS___"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR}/infrastructure"
)
assert os.path.isfile(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR}/CMakeLists.txt"
) and os.path.isfile(
    f"{TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR}/CMakePresets.json"
)

TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR = os.path.realpath(
    f"{INSTALL_TESTS_DIR_PATH}/find_package_exact_version_test"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR}/waypoint_install_linux_clang_2dp6n2H9O8te806G___"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR}/waypoint_install_linux_gcc_vo44y7Bxqbn3kKZA___"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR}/waypoint_install_linux_clang_shared_kd2bzSgxWMh8xpx8___"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR}/waypoint_install_linux_gcc_shared_zogAXLEQwWHTZO9T___"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR = os.path.realpath(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR}/infrastructure"
)
assert os.path.isfile(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR}/CMakeLists.txt"
) and os.path.isfile(
    f"{TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR}/CMakePresets.json"
)

TEST_INSTALL_ADD_SUBDIRECTORY_DIR = os.path.realpath(
    f"{INSTALL_TESTS_DIR_PATH}/add_subdirectory_test"
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/waypoint_sources_4XF31O1T1ff3B3Tq___"
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/waypoint_build_clang_KGgicppoHf0mkVdJ___"
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/waypoint_build_gcc_ZcvFQuKcWaEwFis9___"
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/waypoint_build_clang_shared_ZKPQ5F48VyGbWfTq___"
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_SHARED_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/waypoint_build_gcc_shared_uDavOddLQYiP7PUc___"
)
TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR = os.path.realpath(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_DIR}/infrastructure"
)
assert os.path.isfile(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR}/CMakeLists.txt"
) and os.path.isfile(
    f"{TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR}/CMakePresets.json"
)

EXAMPLES_DIR_PATH = os.path.realpath(f"{PROJECT_ROOT_DIR}/examples")
EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR = os.path.realpath(
    f"{EXAMPLES_DIR_PATH}/quick_start_build_and_install"
)
EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR = os.path.realpath(
    f"{EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR}/waypoint_install___"
)

EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR = os.path.realpath(
    f"{EXAMPLES_DIR_PATH}/quick_start_add_subdirectory"
)
EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR = os.path.realpath(
    f"{EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR}/third_party___"
)
EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR = os.path.realpath(
    f"{EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR}/waypoint"
)

JOBS = os.process_cpu_count() if "process_cpu_count" in dir(os) else os.cpu_count()

COPYRIGHT_HOLDER_NAME = "Wojciech Kałuża"
EXPECTED_SPDX_LICENSE_ID = "MIT"

CLANG20_ENV_PATCH = {"CC": "clang-20", "CXX": "clang++-20"}
GCC15_ENV_PATCH = {"CC": "gcc-15", "CXX": "g++-15"}
EXPORT_COMPILE_COMMANDS_ENV_PATCH = {"CMAKE_EXPORT_COMPILE_COMMANDS": "TRUE"}


@dataclasses.dataclass(frozen=True)
class ModeConfig:
    clean: bool = False
    check_legal: bool = False
    check_formatting: bool = False
    fix_formatting: bool = False
    static_lib: bool = False
    shared_lib: bool = False
    clang: bool = False
    gcc: bool = False
    debug: bool = False
    release: bool = False
    static_analysis: bool = False
    test: bool = False
    test_target: bool = False
    valgrind: bool = False
    coverage: bool = False
    misc: bool = False
    examples: bool = False
    install: bool = False
    test_install: bool = False


@enum.unique
class Mode(enum.Enum):
    Fast = ModeConfig(
        static_lib=True,
        clang=True,
        debug=True,
        test=True,
    )
    Format = ModeConfig(
        fix_formatting=True,
    )
    Full = ModeConfig(
        check_legal=True,
        check_formatting=True,
        static_lib=True,
        shared_lib=True,
        clang=True,
        gcc=True,
        debug=True,
        release=True,
        static_analysis=True,
        test=True,
        test_target=True,
        valgrind=True,
        coverage=True,
        misc=True,
        examples=True,
        install=True,
        test_install=True,
    )
    Clean = ModeConfig(
        clean=True,
    )
    Verify = ModeConfig(
        clean=True,
        check_legal=True,
        check_formatting=True,
        static_lib=True,
        shared_lib=True,
        clang=True,
        gcc=True,
        debug=True,
        release=True,
        static_analysis=True,
        test=True,
        test_target=True,
        valgrind=True,
        coverage=True,
        misc=True,
        examples=True,
        install=True,
        test_install=True,
    )
    Coverage = ModeConfig(
        gcc=True,
        coverage=True,
    )
    StaticAnalysis = ModeConfig(
        clang=True,
        static_analysis=True,
    )
    Valgrind = ModeConfig(
        clang=True,
        gcc=True,
        valgrind=True,
    )

    def __init__(self, config):
        self.config = config

    def __str__(self):
        if self == Mode.Clean:
            return "clean"
        if self == Mode.Coverage:
            return "coverage"
        if self == Mode.Fast:
            return "fast"
        if self == Mode.Format:
            return "format"
        if self == Mode.Full:
            return "full"
        if self == Mode.StaticAnalysis:
            return "static"
        if self == Mode.Valgrind:
            return "valgrind"
        if self == Mode.Verify:
            return "verify"

        assert False, "This should not happen"

    @property
    def clean(self):
        return self.config.clean

    @property
    def incremental(self):
        return not self.config.clean

    @property
    def check_legal(self):
        return self.config.check_legal

    @property
    def check_formatting(self):
        return self.config.check_formatting

    @property
    def fix_formatting(self):
        return self.config.fix_formatting

    @property
    def static_lib(self):
        return self.config.static_lib

    @property
    def shared_lib(self):
        return self.config.shared_lib

    @property
    def clang(self):
        return self.config.clang

    @property
    def gcc(self):
        return self.config.gcc

    @property
    def debug(self):
        return self.config.debug

    @property
    def release(self):
        return self.config.release

    @property
    def static_analysis(self):
        return self.config.static_analysis

    @property
    def test(self):
        return self.config.test

    @property
    def test_target(self):
        return self.config.test_target

    @property
    def valgrind(self):
        return self.config.valgrind

    @property
    def coverage(self):
        return self.config.coverage

    @property
    def misc(self):
        return self.config.misc

    @property
    def examples(self):
        return self.config.examples

    @property
    def install(self):
        return self.config.install

    @property
    def test_install(self):
        return self.config.test_install


@enum.unique
class CMakePresets(enum.Enum):
    LinuxClang = ("configure_linux_clang", "build_linux_clang", "test_linux_clang")
    LinuxGcc = ("configure_linux_gcc", "build_linux_gcc", "test_linux_gcc")
    LinuxClangShared = (
        "configure_linux_clang_shared",
        "build_linux_clang_shared",
        "test_linux_clang_shared",
    )
    LinuxGccShared = (
        "configure_linux_gcc_shared",
        "build_linux_gcc_shared",
        "test_linux_gcc_shared",
    )
    LinuxGccCoverage = (
        "configure_linux_gcc_coverage",
        "build_linux_gcc_coverage",
        "test_linux_gcc_coverage",
    )
    Example = (
        "example_configure",
        "example_build",
        "example_test",
    )
    ExampleShared = (
        "example_configure_shared",
        "example_build_shared",
        "example_test_shared",
    )

    def __init__(self, configure_preset, build_preset, test_preset):
        self._configure_preset = configure_preset
        self._build_preset = build_preset
        self._test_preset = test_preset

    @property
    def configure(self):
        return self._configure_preset

    @property
    def build(self):
        return self._build_preset

    @property
    def test(self):
        return self._test_preset


@enum.unique
class CMakeBuildConfig(enum.Enum):
    Debug = ("Debug",)
    RelWithDebInfo = ("RelWithDebInfo",)
    Release = ("Release",)

    def __init__(self, config_name_):
        self._config_name = config_name_

    def __str__(self):
        return self._config_name


class NewEnv:
    def __init__(self, env):
        self.backup = os.environ.copy()
        self.env = env

    def __enter__(self):
        os.environ.clear()
        os.environ.update(self.env)

        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.environ.clear()
        os.environ.update(self.backup)

        return False


def ns_to_string(nanos) -> str:
    one_second_ns = 10**9
    one_minute_ns = 60 * one_second_ns
    one_hour_ns = 60 * one_minute_ns
    one_day_ns = 24 * one_hour_ns

    if nanos > one_day_ns:
        days = int(nanos / one_day_ns)
        hours = int((nanos % one_day_ns) / one_hour_ns)
        minutes = int((nanos % one_hour_ns) / one_minute_ns)

        return f"{days}d {hours}h {minutes}m"
    if nanos > one_hour_ns:
        hours = int(nanos / one_hour_ns)
        minutes = int((nanos % one_hour_ns) / one_minute_ns)
        seconds = int((nanos % one_minute_ns) / one_second_ns)

        return f"{hours}h {minutes}m {seconds}s"
    if nanos > one_minute_ns:
        minutes = int(nanos / one_minute_ns)
        seconds = int((nanos % one_minute_ns) / one_second_ns)

        return f"{minutes}m {seconds}s"
    if nanos > one_second_ns:
        return f"{round(nanos / one_second_ns, 1)}s"
    if nanos > 10**6:
        return f"{round(nanos / 10 ** 6, 1)}ms"
    if nanos > 10**3:
        return f"{round(nanos / 10 ** 3, 1)}us"

    return f"{nanos}ns"


def run(cmd) -> typing.Tuple[bool, str | None]:
    with tempfile.TemporaryFile("r+") as f:
        try:
            result = subprocess.run(cmd, stdout=f, stderr=f)
        except FileNotFoundError:
            return False, None

        output = "\n"
        f.seek(0)
        output += f.read()
        output += "\n"

        return (result.returncode == 0), output


def is_linux():
    return platform.system() == "Linux"


def check_headers_contain_pragma_once_() -> bool:
    files = find_files_by_name(PROJECT_ROOT_DIR, is_cpp_header_file)
    for f in files:
        with open(f, "r") as file:
            lines = file.readlines()
            lines = [
                line.strip()
                for line in lines
                if re.match(r"^#pragma once$", line.strip()) is not None
            ]
            if len(lines) != 1:
                print(f'Error ({f}):\n"#pragma once" not found')

                return False

    return True


def check_no_spaces_in_paths_() -> bool:
    files = find_files_by_name(PROJECT_ROOT_DIR, lambda x: True)

    for f in files:
        assert f.startswith(PROJECT_ROOT_DIR)
    files = [f[len(PROJECT_ROOT_DIR) + 1 :] for f in files]

    for f in files:
        if " " in f:
            print(f"Error ({f}):\nNo spaces allowed in file paths")

            return False

    return True


def check_main_header_has_no_includes_() -> bool:
    with open(MAIN_HEADER_PATH, "r") as f:
        contents = f.read()

    return re.search(r"# *include", contents) is None


def verify_installation_contents_static_(preset) -> bool:
    install_dir = install_dir_from_preset(preset)

    expected_files = [
        "cmake/waypoint-config.cmake",
        "cmake/waypoint-config-debug.cmake",
        "cmake/waypoint-config-relwithdebinfo.cmake",
        "cmake/waypoint-config-release.cmake",
        "cmake/waypoint-config-version.cmake",
        "include/waypoint/waypoint.hpp",
        "lib/Debug/libassert.a",
        "lib/Debug/libcoverage.a",
        "lib/Debug/libprocess.a",
        "lib/Debug/libwaypoint_impl.a",
        "lib/Debug/libwaypoint_main_impl.a",
        "lib/RelWithDebInfo/libassert.a",
        "lib/RelWithDebInfo/libcoverage.a",
        "lib/RelWithDebInfo/libprocess.a",
        "lib/RelWithDebInfo/libwaypoint_impl.a",
        "lib/RelWithDebInfo/libwaypoint_main_impl.a",
        "lib/Release/libassert.a",
        "lib/Release/libcoverage.a",
        "lib/Release/libprocess.a",
        "lib/Release/libwaypoint_impl.a",
        "lib/Release/libwaypoint_main_impl.a",
    ]

    files = find_files_by_name(install_dir, lambda x: True)
    for expected in expected_files:
        assert (
            os.path.realpath(f"{install_dir}/{expected}") in files
        ), f"File not found: {os.path.realpath(f'{install_dir}/{expected}')}"

    assert len(files) == len(expected_files), "Unexpected files are present"

    return True


def verify_installation_contents_shared_(preset) -> bool:
    install_dir = install_dir_from_preset(preset)

    expected_files = [
        "cmake/waypoint-config.cmake",
        "cmake/waypoint-config-debug.cmake",
        "cmake/waypoint-config-relwithdebinfo.cmake",
        "cmake/waypoint-config-release.cmake",
        "cmake/waypoint-config-version.cmake",
        "include/waypoint/waypoint.hpp",
        "lib/Debug/libwaypoint_impl.so",
        "lib/Debug/libwaypoint_main_impl.so",
        "lib/RelWithDebInfo/libwaypoint_impl.so",
        "lib/RelWithDebInfo/libwaypoint_main_impl.so",
        "lib/Release/libwaypoint_impl.so",
        "lib/Release/libwaypoint_main_impl.so",
    ]

    files = find_files_by_name(install_dir, lambda x: True)
    for expected in expected_files:
        assert (
            os.path.realpath(f"{install_dir}/{expected}") in files
        ), f"File not found: {os.path.realpath(f'{install_dir}/{expected}')}"

    assert len(files) == len(expected_files), "Unexpected files are present"

    return True


def misc_checks_fn() -> bool:
    success = check_main_header_has_no_includes_()
    if not success:
        print(f"Error: Header {MAIN_HEADER_PATH} must not include other headers")

        return False

    success = check_no_spaces_in_paths_()
    if not success:
        print("Error: file paths must not contain spaces")

        return False

    success = check_headers_contain_pragma_once_()
    if not success:
        print('Error: not all headers contain a "#pragma once" include guard')

        return False

    return True


def verify_install_contents_static_fn() -> bool:
    success = verify_installation_contents_static_(CMakePresets.LinuxClang)
    if not success:
        print("Error: Invalid Clang installation contents (static)")

        return False

    success = verify_installation_contents_static_(CMakePresets.LinuxGcc)
    if not success:
        print("Error: Invalid GCC installation contents (static)")

        return False

    return True


def verify_install_contents_shared_fn() -> bool:
    success = verify_installation_contents_shared_(CMakePresets.LinuxClangShared)
    if not success:
        print("Error: Invalid Clang installation contents (dynamic)")

        return False

    success = verify_installation_contents_shared_(CMakePresets.LinuxGccShared)
    if not success:
        print("Error: Invalid GCC installation contents (dynamic)")

        return False

    return True


def dir_from_preset(dir_key, preset, cmake_source_dir) -> str:
    presets_path = os.path.realpath(f"{cmake_source_dir}/CMakePresets.json")
    with open(presets_path) as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset.configure
        ]
        assert len(configure_presets) == 1
        configure_presets = configure_presets[0]

        dir_path = configure_presets[dir_key]
        dir_path = dir_path.replace("${sourceDir}", f"{cmake_source_dir}")

        return os.path.realpath(dir_path)


def build_dir_from_preset(preset, cmake_source_dir) -> str:
    return dir_from_preset("binaryDir", preset, cmake_source_dir)


def install_dir_from_preset(preset) -> str:
    return dir_from_preset("installDir", preset, CMAKE_SOURCE_DIR)


def remove_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)


def create_dir(path) -> bool:
    if os.path.exists(path) and not os.path.isdir(path):
        return False

    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    return True


def clean_build_dir(preset, cmake_source_dir):
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    remove_dir(build_dir)


def clean_install_dir(preset):
    install_dir = install_dir_from_preset(preset)
    remove_dir(install_dir)


def find_files_by_name(dir_path, pred) -> typing.List[str]:
    output = []
    for root, dirs, files in os.walk(dir_path):
        indices_to_remove = []
        for i, d in enumerate(dirs):
            if d.startswith("."):
                indices_to_remove.append(i)
                continue
            if "___" in d:
                indices_to_remove.append(i)
                continue
        indices_to_remove.sort()
        indices_to_remove.reverse()
        for i in indices_to_remove:
            dirs.pop(i)

        indices_to_remove = []
        for i, f in enumerate(files):
            if f.startswith("."):
                indices_to_remove.append(i)
                continue
            if "___" in f:
                indices_to_remove.append(i)
                continue
        indices_to_remove.sort()
        indices_to_remove.reverse()
        for i in indices_to_remove:
            files.pop(i)

        for f in files:
            path = os.path.realpath(os.path.join(root, f))
            if pred(path):
                output.append(path)

    output.sort()

    return output


def install_cmake(preset, config, working_dir) -> bool:
    with contextlib.chdir(working_dir):
        success, output = run(
            [
                "cmake",
                "--build",
                "--preset",
                f"{preset.build}",
                "--target",
                "install",
                "--config",
                f"{config}",
            ]
        )
        if not success:
            if output is not None:
                print(output)

            return False

    return True


def install_gcc_debug_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGcc, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_gcc_relwithdebinfo_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGcc, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_gcc_release_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGcc, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_clang_debug_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClang, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_clang_relwithdebinfo_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClang, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_clang_release_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClang, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_example_clang_debug_fn() -> bool:
    return install_cmake(CMakePresets.Example, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR)


def install_example_clang_relwithdebinfo_fn() -> bool:
    return install_cmake(
        CMakePresets.Example, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_example_clang_release_fn() -> bool:
    return install_cmake(
        CMakePresets.Example, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_example_clang_debug_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.ExampleShared, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_example_clang_relwithdebinfo_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.ExampleShared, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_example_clang_release_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.ExampleShared, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_gcc_debug_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGccShared, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_gcc_relwithdebinfo_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGccShared, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_gcc_release_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxGccShared, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_clang_debug_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClangShared, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_clang_relwithdebinfo_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClangShared, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_clang_release_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.LinuxClangShared, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def configure_cmake_clang_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxClang, CLANG20_ENV_PATCH, CMAKE_SOURCE_DIR)


def configure_cmake_gcc_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxGcc, GCC15_ENV_PATCH, CMAKE_SOURCE_DIR)


def configure_cmake_clang_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared, CLANG20_ENV_PATCH, CMAKE_SOURCE_DIR
    )


def configure_cmake_gcc_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared, GCC15_ENV_PATCH, CMAKE_SOURCE_DIR
    )


def configure_example_clang_fn() -> bool:
    return configure_cmake(CMakePresets.Example, CLANG20_ENV_PATCH, CMAKE_SOURCE_DIR)


def configure_example_clang_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.ExampleShared, CLANG20_ENV_PATCH, CMAKE_SOURCE_DIR
    )


def configure_cmake(preset, env_patch, cmake_source_dir) -> bool:
    env = os.environ.copy()
    env.update(env_patch)
    with NewEnv(env):
        build_dir = build_dir_from_preset(preset, cmake_source_dir)

        if os.path.exists(build_dir):
            return True

        os.mkdir(build_dir)

        with contextlib.chdir(cmake_source_dir):
            command = ["cmake", "--preset", f"{preset.configure}"]
            success, output = run(command)
            if not success:
                if output is not None:
                    print(output)

                return False

    return True


def build_cmake(config, preset, env_patch, cmake_source_dir, target) -> bool:
    env = os.environ.copy()
    env.update(env_patch)
    with NewEnv(env):
        with contextlib.chdir(cmake_source_dir):
            success, output = run(
                [
                    "cmake",
                    "--build",
                    "--preset",
                    f"{preset.build}",
                    "--config",
                    f"{config}",
                    "--target",
                    f"{target}",
                    "--parallel",
                    f"{JOBS}",
                ]
            )
            if not success:
                if output is not None:
                    print(output)

                return False

    return True


def run_ctest(
    preset, build_config, jobs, label_include_regex, cmake_source_dir
) -> bool:
    with contextlib.chdir(cmake_source_dir):
        cmd = [
            "ctest",
            "--preset",
            preset.test,
            "--build-config",
            f"{build_config}",
            "--parallel",
            f"{jobs}",
        ]
        if label_include_regex is not None:
            cmd += [
                "--label-regex",
                label_include_regex,
            ]

        success, output = run(cmd)
        if not success:
            if output is not None:
                print(output)

            return False

    return True


def clang_tidy_process_single_file(data) -> typing.Tuple[bool, str, float, str | None]:
    file, build_dir = data

    start_time = time.time_ns()
    success, output = run(
        [
            "clang-tidy-20",
            f"--config-file={INFRASTRUCTURE_DIR}/.clang-tidy-20",
            "-p",
            build_dir,
            file,
        ]
    )
    duration = time.time_ns() - start_time

    return (
        success,
        file,
        duration,
        None if success else (None if output is None else output.strip()),
    )


def run_clang_static_analysis_(files) -> bool:
    success = run_clang_tidy(CMakePresets.LinuxClang, CMAKE_SOURCE_DIR, files)
    if not success:
        return False

    # Test installs

    success = run_clang_tidy(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        files,
    )
    if not success:
        return False

    success = run_clang_tidy(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        files,
    )
    if not success:
        return False

    success = run_clang_tidy(
        CMakePresets.LinuxClang, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR, files
    )
    if not success:
        return False

    # Examples

    success = run_clang_tidy(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        files,
    )
    if not success:
        return False

    success = run_clang_tidy(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        files,
    )
    if not success:
        return False

    return True


def run_clang_static_analysis_all_files_fn() -> bool:
    files = set(find_files_by_name(PROJECT_ROOT_DIR, is_cpp_source_file))

    return run_clang_static_analysis_(files)


def run_clang_static_analysis_changed_files_fn() -> bool:
    files = set(changed_cpp_source_files_and_dependents(CMakePresets.LinuxClang))

    return run_clang_static_analysis_(files)


def run_clang_tidy(preset, cmake_source_dir, all_files) -> bool:
    files_from_db = get_files_from_compilation_database(preset, cmake_source_dir)
    files_from_db = [f for f in files_from_db if f in all_files]
    if len(files_from_db) == 0:
        return True

    build_dir = build_dir_from_preset(preset, cmake_source_dir)

    inputs = [(f, build_dir) for f in files_from_db]
    with multiprocessing.Pool(JOBS) as pool:
        results = pool.map(clang_tidy_process_single_file, inputs)

        errors = [
            (file, stdout) for success, file, duration, stdout in results if not success
        ]
        if len(errors) > 0:
            for f, stdout in errors:
                print(f"Error running clang-tidy on {f}")
                if stdout is not None:
                    print(stdout)

            return False

    return True


def test_gcc_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc, CMakeBuildConfig.Debug, JOBS, r"^test$", CMAKE_SOURCE_DIR
    )


def test_gcc_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_release_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_release_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_debug_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_relwithdebinfo_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_release_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_debug_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_relwithdebinfo_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_release_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^valgrind$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^valgrind$",
        CMAKE_SOURCE_DIR,
    )


def run_lcov(build_dir) -> bool:
    success = create_dir(COVERAGE_DIR_LCOV)
    if not success:
        print(f"Failed to create {COVERAGE_DIR_LCOV}")

        return False

    with contextlib.chdir(PROJECT_ROOT_DIR):
        success, output = run(
            [
                "lcov",
                "--branch-coverage",
                "--capture",
                "--directory",
                build_dir,
                "--exclude",
                f"{PROJECT_ROOT_DIR}/test/",
                "--function-coverage",
                "--ignore-errors",
                "inconsistent",
                "--include",
                PROJECT_ROOT_DIR,
                "--output-file",
                COVERAGE_FILE_LCOV,
            ]
        )
        if not success:
            print("Error running lcov")
            if output is not None:
                print(output)

            return False

        success, output = run(
            [
                "genhtml",
                "--branch-coverage",
                "--dark-mode",
                "--flat",
                "--function-coverage",
                "--ignore-errors",
                "inconsistent",
                "--legend",
                "--output-directory",
                COVERAGE_DIR_LCOV,
                "--show-zero-columns",
                "--sort",
                COVERAGE_FILE_LCOV,
            ]
        )
        if not success:
            print("Error running genhtml")
            if output is not None:
                print(output)

            return False

    return True


def run_gcovr(build_dir) -> bool:
    success = create_dir(COVERAGE_DIR_GCOVR)
    if not success:
        print(f"Failed to create {COVERAGE_DIR_GCOVR}")

        return False

    with contextlib.chdir(PROJECT_ROOT_DIR):
        success, output = run(
            [
                "gcovr",
                "--decisions",
                "--exclude-pattern-prefix",
                "GCOV_COVERAGE_58QuSuUgMN8onvKx_*",
                "--exclude",
                f"{PROJECT_ROOT_DIR}/test/",
                "--filter",
                PROJECT_ROOT_DIR,
                "--gcov-object-directory",
                build_dir,
                "--html-details",
                COVERAGE_FILE_HTML_GCOVR,
                "--html-theme",
                "github.dark-green",
                "--json-summary",
                COVERAGE_FILE_JSON_GCOVR,
                "--json-summary-pretty",
                "--root",
                PROJECT_ROOT_DIR,
                "--sort",
                "uncovered-percent",
                "--verbose",
            ]
        )
        if not success:
            print("Error running gcovr")
            if output is not None:
                print(output)

            return False

    return True


def process_coverage_fn() -> bool:
    build_dir = build_dir_from_preset(CMakePresets.LinuxGccCoverage, CMAKE_SOURCE_DIR)

    success = run_lcov(build_dir)
    if not success:
        return False

    success = run_gcovr(build_dir)
    if not success:
        return False

    return True


def configure_cmake_gcc_coverage_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccCoverage, GCC15_ENV_PATCH, CMAKE_SOURCE_DIR
    )


def build_gcc_coverage_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccCoverage,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_coverage_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccCoverage,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_gcc_coverage_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccCoverage,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def analyze_gcc_coverage_fn() -> bool:
    with open(COVERAGE_FILE_JSON_GCOVR, "r") as f:
        data = json.load(f)

    all_branches_covered = data["branch_covered"] == data["branch_total"]
    all_decisions_covered = data["decision_covered"] == data["decision_total"]
    all_functions_covered = data["function_covered"] == data["function_total"]
    all_lines_covered = data["line_covered"] == data["line_total"]

    if (
        not all_branches_covered
        or not all_decisions_covered
        or not all_functions_covered
        or not all_lines_covered
    ):
        print("Incomplete coverage")
        return False

    return True


def build_example_clang_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.ExampleShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.ExampleShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.ExampleShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_relwithdebinfo_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_release_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_debug_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_relwithdebinfo_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_release_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def is_bash_file(f) -> bool:
    return re.search(r"\.bash$", f) is not None


def is_cmake_file(f) -> bool:
    return (
        re.search(r"CMakeLists\.txt$", f) is not None
        or re.search(r"\.cmake$", f) is not None
    )


def is_cpp_header_file(f) -> bool:
    return re.search(r"\.hpp$", f) is not None


def is_cpp_source_file(f) -> bool:
    return re.search(r"\.cpp$", f) is not None


def is_cpp_file(f) -> bool:
    return is_cpp_source_file(f) or is_cpp_header_file(f)


def is_docker_file(f) -> bool:
    return (
        re.search(r"\.dockerfile$", f) is not None
        or re.search(r"^Dockerfile$", os.path.basename(f)) is not None
    )


def is_json_file(f) -> bool:
    return re.search(r"\.json$", f) is not None


def is_python_file(f) -> bool:
    return re.search(r"\.py$", f) is not None


def is_file_with_licensing_comment(f) -> bool:
    return (
        is_bash_file(f)
        or is_cmake_file(f)
        or is_cpp_file(f)
        or is_docker_file(f)
        or is_python_file(f)
    )


def match_copyright_notice_pattern(text: str):
    return re.match(r"^(?://|#) (Copyright \(c\) [0-9]{4}[\- ].+)$", text)


def match_spdx_license_id_pattern(line):
    return re.match(r"^(?://|#) SPDX-License-Identifier: (.+)$", line)


def check_copyright_comments_in_single_file(
    file,
) -> typing.Tuple[bool, str | None, str]:
    with open(file, "r") as f:
        lines = f.readlines()
    lines = lines[0:3]
    lines = [line.strip() for line in lines]
    copyright_lines = [
        line for line in lines if match_copyright_notice_pattern(line) is not None
    ]
    if len(copyright_lines) != 1:
        return (
            False,
            f"Error ({file}):\n"
            "Notice of copyright not found or multiple lines matched in error",
            file,
        )

    copyright_notice = match_copyright_notice_pattern(copyright_lines[0]).group(1)
    success, error_output = validate_notice_of_copyright(file, copyright_notice)
    if not success:
        return False, error_output, file

    spdx_license_id_lines = [
        line for line in lines if match_spdx_license_id_pattern(line) is not None
    ]
    if len(spdx_license_id_lines) != 1:
        return (
            False,
            f"Error ({file}):\n"
            "SPDX-License-Identifier not found or multiple lines matched in error",
            file,
        )

    spdx_license_id = match_spdx_license_id_pattern(spdx_license_id_lines[0]).group(1)
    if spdx_license_id != EXPECTED_SPDX_LICENSE_ID:
        return (
            False,
            f"Error ({file}):\n"
            "Unexpected SPDX-License-Identifier: "
            f"expected {EXPECTED_SPDX_LICENSE_ID}, found {spdx_license_id}",
            file,
        )

    license_file_ref_lines = [
        line
        for line in lines
        if re.match(r"^(?://|#) For license details, see LICENSE file$", line)
        is not None
    ]
    if len(license_file_ref_lines) != 1:
        return (
            False,
            f"Error ({file}):\n"
            "Reference to LICENSE file not found or multiple lines matched in error",
            file,
        )

    return True, None, file


def check_copyright_comments_(files) -> bool:
    with multiprocessing.Pool(JOBS) as pool:
        results = pool.map(check_copyright_comments_in_single_file, files)
    errors = [(output, file) for success, output, file in results if not success]
    if len(errors) > 0:
        for output, file in errors:
            print(f"Error: {file}\nIncorrect copyright comment")
            if output is not None:
                print(output)

        return False

    return True


def check_copyright_comments_fn() -> bool:
    files = find_files_by_name(PROJECT_ROOT_DIR, is_file_with_licensing_comment)

    return check_copyright_comments_(files)


def check_formatting_in_single_file(file: str) -> typing.Tuple[bool, str | None, str]:
    if is_cmake_file(file):
        success, output = check_formatting_cmake(file)

        return success, output, file
    if is_cpp_file(file):
        success, output = check_formatting_cpp(file)

        return success, output, file
    if is_json_file(file):
        success, output = check_formatting_json(file)

        return success, output, file
    if is_python_file(file):
        success, output = check_formatting_python(file)

        return success, output, file

    return False, "Expected to check formatting in unsupported file type\n", file


def format_single_file(f) -> typing.Tuple[bool, str | None, str]:
    if is_cmake_file(f):
        success, output = format_cmake(f)

        return success, output, f
    if is_cpp_file(f):
        success, output = format_cpp(f)

        return success, output, f
    if is_json_file(f):
        success, output = format_json(f)

        return success, output, f
    if is_python_file(f):
        success, output = format_python(f)

        return success, output, f

    return False, "Expected to format unsupported file type\n", f


def is_file_for_formatting(f) -> bool:
    return is_cmake_file(f) or is_cpp_file(f) or is_json_file(f) or is_python_file(f)


def check_formatting_fn() -> bool:
    files = find_files_by_name(PROJECT_ROOT_DIR, is_file_for_formatting)

    with multiprocessing.Pool(JOBS) as pool:
        results = pool.map(check_formatting_in_single_file, files)
        errors = [(output, file) for success, output, file in results if not success]
        if len(errors) > 0:
            for output, file in errors:
                if output is not None:
                    print(output)
                print(
                    f'Error: {file}\nIncorrect formatting; run the build in "format" mode'
                )

            return False

    return True


def format_sources_fn() -> bool:
    files = find_files_by_name(PROJECT_ROOT_DIR, is_file_for_formatting)

    with multiprocessing.Pool(JOBS) as pool:
        results = pool.map(format_single_file, files)
        errors = [(output, file) for success, output, file in results if not success]
        if len(errors) > 0:
            for output, file in errors:
                if output is not None:
                    print(output)
                print(f"Error formatting file {file}")

            return False

    return True


def check_formatting_cmake(f) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "--check",
            f,
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_cpp(file) -> typing.Tuple[bool, str | None]:
    path_to_config = os.path.realpath(f"{INFRASTRUCTURE_DIR}/.clang-format-20")

    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "--dry-run",
            "-Werror",
            file,
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_json(f) -> typing.Tuple[bool, str | None]:
    with open(f, "r") as handle:
        original = handle.read()
    with open(f, "r") as handle:
        data = json.load(handle)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"

    success = data_str == original
    if not success:
        return False, "Incorrect JSON file formatting\n"

    return True, None


def check_formatting_python(file) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [PYTHON, "-m", "isort", "--check", "--line-length", "88", file]
    )
    if not success:
        return False, output

    success, output = run(["black", "--quiet", "--check", "--line-length", "88", file])
    if not success:
        return False, output

    return True, None


def format_cmake(f) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "-i",
            f,
        ]
    )
    if not success:
        return False, output

    return True, None


def format_cpp(f) -> typing.Tuple[bool, str | None]:
    path_to_config = os.path.realpath(f"{INFRASTRUCTURE_DIR}/.clang-format-20")

    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "-i",
            f,
        ]
    )
    if not success:
        return False, output

    return True, None


def format_json(f) -> typing.Tuple[bool, str | None]:
    with open(f, "r") as handle:
        original = handle.read()
    with open(f, "r") as handle:
        data = json.load(handle)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"
    if data_str != original:
        with open(f, "w") as handle:
            handle.write(data_str)

    return True, None


def format_python(f) -> typing.Tuple[bool, str | None]:
    success, output = run([PYTHON, "-m", "isort", "--line-length", "88", f])
    if not success:
        return False, output

    success, output = run(["black", "--quiet", "--line-length", "88", f])
    if not success:
        return False, output

    return True, None


def invert_index(index) -> typing.Dict[str, typing.Set[str]]:
    output = {}
    for file in index.keys():
        deps = index[file]
        for d in deps:
            if d not in output.keys():
                output[d] = set()
            output[d].add(file)
            output[d].add(d)

    return output


def process_depfiles(depfile_paths) -> typing.Dict[str, typing.Set[str]]:
    index = {}
    for path in depfile_paths:
        with open(path, "r") as f:
            lines = f.readlines()
        lines = lines[1:]
        lines = [l.lstrip(" ").rstrip(" \\\n") for l in lines]
        paths = []
        for l in lines:
            if " " in l:
                for x in l.split(" "):
                    paths.append(x)
                continue
            paths.append(l)

        paths = [os.path.realpath(p) for p in paths if os.path.isfile(p)]
        paths = [p for p in paths if p.startswith(f"{PROJECT_ROOT_DIR}/")]

        cpp_file = paths[0]

        if cpp_file not in index.keys():
            index[cpp_file] = set()

        index[cpp_file].update(paths)

    return index


def get_changed_files(predicate) -> typing.List[str]:
    with contextlib.chdir(PROJECT_ROOT_DIR):
        success1, output1 = run(["git", "diff", "--name-only"])
        success2, output2 = run(["git", "diff", "--cached", "--name-only"])
        success3, output3 = run(["git", "ls-files", "--others", "--exclude-standard"])
        # Fall back to all files if git is not available
        if not (success1 and success2 and success3):
            return find_files_by_name(PROJECT_ROOT_DIR, predicate)

        files = output1.strip().split("\n")
        files += output2.strip().split("\n")
        files += output3.strip().split("\n")
        out = []
        for f in files:
            path = os.path.realpath(f"{PROJECT_ROOT_DIR}/{f.strip()}")
            if os.path.isfile(path) and predicate(path):
                out.append(path)

        out = list(set(out))
        out.sort()

        return out


def collect_depfiles(preset):
    build_dir = build_dir_from_preset(preset, CMAKE_SOURCE_DIR)
    depfiles = []
    for root, dirs, files in os.walk(build_dir):
        for f in files:
            depfiles.append(f"{root}/{f}")
    depfiles = [
        os.path.realpath(f)
        for f in depfiles
        if os.path.isfile(f) and re.search(r"\.o\.d$", f) is not None
    ]
    depfiles.sort()

    return depfiles


def changed_cpp_source_files_and_dependents(preset) -> typing.List[str]:
    changed_cpp_files = get_changed_files(is_cpp_file)
    if len(changed_cpp_files) == 0:
        return []

    depfiles = collect_depfiles(preset)
    index = process_depfiles(depfiles)
    reverse_index = invert_index(index)
    files_for_analysis = set()
    for changed in changed_cpp_files:
        if changed not in reverse_index.keys():
            continue

        files_for_analysis.update(reverse_index[changed])

    output = list(files_for_analysis)
    output.sort()

    output = [f for f in output if is_cpp_source_file(f)]

    return output


class CliConfig:
    def __init__(self, mode_str):
        self.mode = None

        if mode_str == f"{Mode.Clean}":
            self.mode = Mode.Clean
        if mode_str == f"{Mode.Coverage}":
            self.mode = Mode.Coverage
        if mode_str == f"{Mode.Fast}":
            self.mode = Mode.Fast
        if mode_str == f"{Mode.Format}":
            self.mode = Mode.Format
        if mode_str == f"{Mode.Full}":
            self.mode = Mode.Full
        if mode_str == f"{Mode.StaticAnalysis}":
            self.mode = Mode.StaticAnalysis
        if mode_str == f"{Mode.Valgrind}":
            self.mode = Mode.Valgrind
        if mode_str == f"{Mode.Verify}":
            self.mode = Mode.Verify

        assert self.mode is not None


def preamble() -> tuple[CliConfig | None, bool]:
    if not is_linux():
        print(f"Unknown OS: {platform.system()}")

        return None, False

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=[
            f"{Mode.Clean}",
            f"{Mode.Coverage}",
            f"{Mode.Fast}",
            f"{Mode.Format}",
            f"{Mode.Full}",
            f"{Mode.StaticAnalysis}",
            f"{Mode.Valgrind}",
            f"{Mode.Verify}",
        ],
        metavar="mode",
        help=f"""Selects build mode:
                 "{Mode.Clean}" deletes the build trees;
                 "{Mode.Coverage}" measures test coverage;
                 "{Mode.Format}" formats source files;
                 "{Mode.Fast}" runs one build and tests for quick iterations;
                 "{Mode.Full}" builds everything and runs all checks;
                 "{Mode.StaticAnalysis}" performs static analysis;
                 "{Mode.Valgrind}" runs Valgrind/memcheck;
                 "{Mode.Verify}" runs "{Mode.Clean}" followed by "{Mode.Full}".""",
    )

    parsed = parser.parse_args()

    config = CliConfig(parsed.mode)

    return config, True


def clean_fn() -> bool:
    clean_build_dir(CMakePresets.LinuxClang, CMAKE_SOURCE_DIR)
    clean_build_dir(CMakePresets.LinuxGcc, CMAKE_SOURCE_DIR)
    clean_build_dir(CMakePresets.LinuxClangShared, CMAKE_SOURCE_DIR)
    clean_build_dir(CMakePresets.LinuxGccShared, CMAKE_SOURCE_DIR)
    clean_build_dir(
        CMakePresets.LinuxClang, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxGcc, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
    clean_build_dir(
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
    clean_build_dir(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
    clean_build_dir(
        CMakePresets.LinuxGcc, TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
    clean_build_dir(
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
    clean_build_dir(
        CMakePresets.LinuxClang, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxGcc, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxClangShared, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    clean_build_dir(
        CMakePresets.LinuxGccShared, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    clean_build_dir(CMakePresets.LinuxGccCoverage, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.LinuxClang)
    clean_install_dir(CMakePresets.LinuxGcc)
    clean_install_dir(CMakePresets.LinuxClangShared)
    clean_install_dir(CMakePresets.LinuxGccShared)
    clean_install_dir(CMakePresets.LinuxGccCoverage)
    remove_dir(COVERAGE_DIR_GCOVR)
    remove_dir(COVERAGE_DIR_LCOV)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_SHARED_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_SHARED_DIR)

    clean_build_dir(CMakePresets.Example, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.Example)
    clean_build_dir(CMakePresets.ExampleShared, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.ExampleShared)
    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR)

    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR)

    return True


def get_files_from_compilation_database(preset, cmake_source_dir) -> typing.List[str]:
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    compilation_db = os.path.realpath(f"{build_dir}/compile_commands.json")

    with open(compilation_db, "r") as f:
        data = json.load(f)

    files = set()

    for d in data:
        files.add(d["file"])

    files = list(files)
    files.sort()

    files = [os.path.realpath(f) for f in files]
    files = [f for f in files if "___" not in f]
    for f in files:
        assert os.path.isfile(f), f"File not found: {f}"

    return files


class Task:
    def __init__(self, name: str, fn: typing.Callable[[], bool] | None = None):
        assert name is not None
        self.name_ = name
        self.fn_ = fn
        self.task_attempted_ = False
        self.deps_success_ = False
        self.success_ = False
        self.dependencies_ = []

    def depends_on(self, deps: typing.List["Task"]):
        for d in deps:
            self.dependencies_.append(d)

    def run(self) -> bool:
        if self.task_attempted_ and not (self.deps_success_ and self.success_):
            return False

        if self.task_attempted_ and self.deps_success_ and self.success_:
            return True

        self.task_attempted_ = True

        start_deps = time.time_ns()

        if len(self.dependencies_) > 0:
            print(f"Preparing task: {self.name_}")
        for d in self.dependencies_:
            success = d.run()
            if not success:
                return False

        self.deps_success_ = True

        print(f"Running task: {self.name_}")
        start = time.time_ns()
        success = True if self.fn_ is None else self.fn_()
        if len(self.dependencies_) > 0:
            print(
                "Finished task:",
                f"{self.name_} ({ns_to_string(time.time_ns() - start)},",
                f"total: {ns_to_string(time.time_ns() - start_deps)})",
            )
        else:
            print(
                "Finished task:",
                f"{self.name_} ({ns_to_string(time.time_ns() - start)})",
            )
        if not success:
            if len(self.dependencies_) > 0:
                print(
                    "Task failed:",
                    f"{self.name_} ({ns_to_string(time.time_ns() - start)},",
                    f"total: {ns_to_string(time.time_ns() - start_deps)})",
                )
            else:
                print(
                    "Task failed:",
                    f"{self.name_} ({ns_to_string(time.time_ns() - start)})",
                )

            return False

        self.success_ = True

        return True


def recursively_copy_dir(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True)


def test_install_find_package_no_version_gcc_copy_artifacts_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxGcc)
    recursively_copy_dir(install_dir, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR)

    return True


def test_install_find_package_no_version_clang_copy_artifacts_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxClang)
    recursively_copy_dir(install_dir, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR)

    return True


def test_install_find_package_no_version_gcc_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_copy_artifacts_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxGcc)
    recursively_copy_dir(install_dir, TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR)

    return True


def test_install_find_package_exact_version_clang_copy_artifacts_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxClang)
    recursively_copy_dir(install_dir, TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR)

    return True


def test_install_find_package_exact_version_gcc_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_copy_artifacts_shared_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxGccShared)
    recursively_copy_dir(
        install_dir, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR
    )

    return True


def test_install_find_package_no_version_clang_copy_artifacts_shared_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxClangShared)
    recursively_copy_dir(
        install_dir, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR
    )

    return True


def test_install_find_package_no_version_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_copy_artifacts_shared_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxGccShared)
    recursively_copy_dir(
        install_dir, TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR
    )

    return True


def test_install_find_package_exact_version_clang_copy_artifacts_shared_fn() -> bool:
    install_dir = install_dir_from_preset(CMakePresets.LinuxClangShared)
    recursively_copy_dir(
        install_dir, TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR
    )

    return True


def test_install_find_package_exact_version_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_test_shared_fn() -> (
    bool
):
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_copy_sources_fn() -> bool:
    recursively_copy_dir(
        INFRASTRUCTURE_DIR,
        f"{TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR}/infrastructure",
    )
    recursively_copy_dir(
        f"{PROJECT_ROOT_DIR}/src",
        f"{TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR}/src",
    )

    return True


def test_install_add_subdirectory_gcc_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_release_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_release_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        JOBS,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_clang_debug_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_relwithdebinfo_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_release_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_debug_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_relwithdebinfo_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_release_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CLANG20_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_debug_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_relwithdebinfo_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_release_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_debug_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_relwithdebinfo_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_release_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        GCC15_ENV_PATCH,
        CMAKE_SOURCE_DIR,
        "test",
    )


def example_quick_start_build_and_install_fn() -> bool:
    example_cmake_source_dir = EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR
    env_patch = CLANG20_ENV_PATCH
    build_dir = build_dir_from_preset(CMakePresets.Example, example_cmake_source_dir)

    # use Waypoint as a static library
    remove_dir(build_dir)
    remove_dir(EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR)

    install_dir = install_dir_from_preset(CMakePresets.Example)
    recursively_copy_dir(
        install_dir, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR
    )

    env = os.environ.copy()
    env.update(EXPORT_COMPILE_COMMANDS_ENV_PATCH)
    with NewEnv(env):
        success = configure_cmake(
            CMakePresets.Example, env_patch, example_cmake_source_dir
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False

        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Debug,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.RelWithDebInfo,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Release,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False

        with contextlib.chdir(example_cmake_source_dir):
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Release}/test_program"]
            )
            if not success:
                return False

    # use Waypoint as a dynamic library
    remove_dir(build_dir)
    remove_dir(EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR)

    install_dir = install_dir_from_preset(CMakePresets.ExampleShared)
    recursively_copy_dir(
        install_dir, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR
    )

    env = os.environ.copy()
    env.update(EXPORT_COMPILE_COMMANDS_ENV_PATCH)
    with NewEnv(env):
        success = configure_cmake(
            CMakePresets.Example, env_patch, example_cmake_source_dir
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False

        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Debug,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.RelWithDebInfo,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Release,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False

        with contextlib.chdir(example_cmake_source_dir):
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Release}/test_program"]
            )
            if not success:
                return False

    return True


def example_quick_start_add_subdirectory_fn() -> bool:
    remove_dir(EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR)
    recursively_copy_dir(
        f"{PROJECT_ROOT_DIR}/infrastructure",
        f"{EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR}/infrastructure",
    )
    recursively_copy_dir(
        f"{PROJECT_ROOT_DIR}/src",
        f"{EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR}/src",
    )

    example_cmake_source_dir = EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    env_patch = CLANG20_ENV_PATCH
    build_dir = build_dir_from_preset(CMakePresets.Example, example_cmake_source_dir)

    env = os.environ.copy()
    env.update(EXPORT_COMPILE_COMMANDS_ENV_PATCH)
    with NewEnv(env):
        success = configure_cmake(
            CMakePresets.Example, env_patch, example_cmake_source_dir
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "all",
        )
        if not success:
            return False

        success = build_cmake(
            CMakeBuildConfig.Debug,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.RelWithDebInfo,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False
        success = build_cmake(
            CMakeBuildConfig.Release,
            CMakePresets.Example,
            env_patch,
            example_cmake_source_dir,
            "test",
        )
        if not success:
            return False

        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Debug,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.RelWithDebInfo,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False
        success = run_ctest(
            CMakePresets.Example,
            CMakeBuildConfig.Release,
            JOBS,
            None,
            example_cmake_source_dir,
        )
        if not success:
            return False

        with contextlib.chdir(example_cmake_source_dir):
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
            )
            if not success:
                return False
            success, output = run(
                [f"{build_dir}/{CMakeBuildConfig.Release}/test_program"]
            )
            if not success:
                return False

    return True


def validate_notice_of_copyright(
    file: str, copyright_notice: str
) -> typing.Tuple[bool, str | None]:
    single_year = re.match(r"^Copyright \(c\) ([0-9]{4}) (.+)$", copyright_notice)
    year_range = re.match(
        r"^Copyright \(c\) ([0-9]{4})-([0-9]{4}) (.+)$", copyright_notice
    )

    if single_year is None and year_range is None:
        return (
            False,
            f"Error ({file}):\n" "Notice of copyright not found or is malformed",
        )

    current_year = datetime.datetime.now().year

    if single_year is not None:
        name = single_year.group(2)
        if name != COPYRIGHT_HOLDER_NAME:
            return (
                False,
                f"Error ({file}):\n"
                f'Unexpected copyright holder name "{name}"'
                f'Expected "{COPYRIGHT_HOLDER_NAME}"',
            )

        start_year = int(single_year.group(1))
        if current_year < start_year:
            return (
                False,
                f"Error ({file}):\n"
                "Year in notice of copyright appears to be in the future "
                f"({start_year}; current year is {current_year})",
            )

        if start_year == current_year:
            return True, None

        return (
            False,
            f"Error ({file}):\n"
            f'Notice of copyright begins with "Copyright (c) {start_year}", '
            f'but it should begin with "Copyright (c) {start_year}-{current_year}"',
        )

    if year_range is not None:
        name = year_range.group(3)
        if name != COPYRIGHT_HOLDER_NAME:
            return (
                False,
                f"Error ({file}):\n"
                f'Unexpected copyright holder name "{name}"'
                f'Expected "{COPYRIGHT_HOLDER_NAME}"',
            )

        start_year = int(year_range.group(1))
        end_year = int(year_range.group(2))
        if end_year <= start_year:
            return (
                False,
                f"Error ({file}):\n"
                f"Malformed year range in notice of copyright ({start_year}-{end_year})",
            )

        if current_year < end_year:
            return (
                False,
                f"Error ({file}):\n"
                "Year in notice of copyright appears to be in the future "
                f"({start_year}-{end_year}; current year is {current_year})",
            )

        if end_year == current_year:
            return True, None

        return (
            False,
            f"Error ({file}):\n"
            f'Notice of copyright begins with "Copyright (c) {start_year}-{end_year}", '
            f'but it should begin with "Copyright (c) {start_year}-{current_year}"',
        )

    return True, None


def check_license_file_fn() -> bool:
    license_file_path = os.path.realpath(f"{PROJECT_ROOT_DIR}/LICENSE")
    if not os.path.isfile(license_file_path):
        print(f"Error: file {license_file_path} does not exist")

        return False

    with open(license_file_path, "br") as f:
        data = f.read()
    sha3_256 = hashlib.sha3_256()
    sha3_256.update(data)
    sha3_256_digest = sha3_256.hexdigest()
    expected_sha3_256_digest = (
        "4885e645412f0073f7c5211e3dd1c581e87e67e6ec1ac33dac1221d3fe66101c"
    )

    if sha3_256_digest != expected_sha3_256_digest:
        print(
            f"Unexpected LICENSE file digest: {sha3_256_digest}\n"
            "Verify the LICENSE file is correct and update the variable "
            f"expected_sha3_256_digest in {os.path.basename(sys.argv[0])}"
        )

        return False

    with open(license_file_path, "r") as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    copyright_lines = [
        line
        for line in lines
        if re.match(r"^Copyright \(c\) [0-9]{4}[\- ].+$", line) is not None
    ]
    if len(copyright_lines) != 1:
        print(
            f"Error ({license_file_path}):\n"
            "Notice of copyright not found or multiple lines matched in error"
        )

        return False

    copyright_notice = copyright_lines[0]
    success, error_output = validate_notice_of_copyright(
        license_file_path, copyright_notice
    )
    if not success:
        print(error_output)

        return False

    return True


def main() -> int:
    config, success = preamble()
    if not success:
        return 1

    mode = config.mode

    test_clang_debug = Task("Test Clang Debug (static)", test_clang_debug_fn)
    test_clang_relwithdebinfo = Task(
        "Test Clang RelWithDebInfo (static)", test_clang_relwithdebinfo_fn
    )
    test_clang_release = Task("Test Clang Release (static)", test_clang_release_fn)
    test_clang_debug_test_target = Task(
        "Build Clang Debug test target (static)", test_clang_debug_test_target_fn
    )
    test_clang_relwithdebinfo_test_target = Task(
        "Build Clang RelWithDebInfo test target (static)",
        test_clang_relwithdebinfo_test_target_fn,
    )
    test_clang_release_test_target = Task(
        "Build Clang Release test target (static)", test_clang_release_test_target_fn
    )
    build_clang_debug_all = Task(
        "Build Clang Debug (static; all)", build_clang_debug_all_fn
    )
    build_clang_debug_all_tests = Task(
        "Build Clang Debug (static; all_tests)", build_clang_debug_all_tests_fn
    )
    build_clang_relwithdebinfo_all = Task(
        "Build Clang RelWithDebInfo (static; all)", build_clang_relwithdebinfo_all_fn
    )
    build_clang_relwithdebinfo_all_tests = Task(
        "Build Clang RelWithDebInfo (static; all_tests)",
        build_clang_relwithdebinfo_all_tests_fn,
    )
    build_clang_release_all = Task(
        "Build Clang Release (static; all)", build_clang_release_all_fn
    )
    build_clang_release_all_tests = Task(
        "Build Clang Release (static; all_tests)", build_clang_release_all_tests_fn
    )

    configure_cmake_clang = Task(
        "Configure CMake for Clang (static)", configure_cmake_clang_fn
    )

    test_clang_debug_shared = Task(
        "Test Clang Debug (dynamic)", test_clang_debug_shared_fn
    )
    test_clang_relwithdebinfo_shared = Task(
        "Test Clang RelWithDebInfo (dynamic)", test_clang_relwithdebinfo_shared_fn
    )
    test_clang_release_shared = Task(
        "Test Clang Release (dynamic)", test_clang_release_shared_fn
    )
    test_clang_debug_test_target_shared = Task(
        "Build Clang Debug test target (dynamic)",
        test_clang_debug_test_target_shared_fn,
    )
    test_clang_relwithdebinfo_test_target_shared = Task(
        "Build Clang RelWithDebInfo test target (dynamic)",
        test_clang_relwithdebinfo_test_target_shared_fn,
    )
    test_clang_release_test_target_shared = Task(
        "Build Clang Release test target (dynamic)",
        test_clang_release_test_target_shared_fn,
    )
    build_clang_debug_all_shared = Task(
        "Build Clang Debug (dynamic; all)", build_clang_debug_all_shared_fn
    )
    build_clang_debug_all_tests_shared = Task(
        "Build Clang Debug (dynamic; all_tests)", build_clang_debug_all_tests_shared_fn
    )
    build_clang_relwithdebinfo_all_shared = Task(
        "Build Clang RelWithDebInfo (dynamic; all)",
        build_clang_relwithdebinfo_all_shared_fn,
    )
    build_clang_relwithdebinfo_all_tests_shared = Task(
        "Build Clang RelWithDebInfo (dynamic; all_tests)",
        build_clang_relwithdebinfo_all_tests_shared_fn,
    )
    build_clang_release_all_shared = Task(
        "Build Clang Release (dynamic; all)", build_clang_release_all_shared_fn
    )
    build_clang_release_all_tests_shared = Task(
        "Build Clang Release (dynamic; all_tests)",
        build_clang_release_all_tests_shared_fn,
    )
    configure_cmake_clang_shared = Task(
        "Configure CMake for Clang (dynamic)", configure_cmake_clang_shared_fn
    )

    build_clang_debug_all.depends_on([configure_cmake_clang])
    build_clang_debug_all_tests.depends_on([build_clang_debug_all])
    test_clang_debug.depends_on([build_clang_debug_all_tests])
    build_clang_relwithdebinfo_all.depends_on([configure_cmake_clang])
    build_clang_relwithdebinfo_all_tests.depends_on([build_clang_relwithdebinfo_all])
    test_clang_relwithdebinfo.depends_on([build_clang_relwithdebinfo_all_tests])
    build_clang_release_all.depends_on([configure_cmake_clang])
    build_clang_release_all_tests.depends_on([build_clang_release_all])
    test_clang_release.depends_on([build_clang_release_all_tests])

    test_clang_debug_test_target.depends_on([build_clang_debug_all_tests])
    test_clang_relwithdebinfo_test_target.depends_on(
        [build_clang_relwithdebinfo_all_tests]
    )
    test_clang_release_test_target.depends_on([build_clang_release_all_tests])

    build_clang_debug_all_shared.depends_on([configure_cmake_clang_shared])
    build_clang_debug_all_tests_shared.depends_on([build_clang_debug_all_shared])
    test_clang_debug_shared.depends_on([build_clang_debug_all_tests_shared])
    build_clang_relwithdebinfo_all_shared.depends_on([configure_cmake_clang_shared])
    build_clang_relwithdebinfo_all_tests_shared.depends_on(
        [build_clang_relwithdebinfo_all_shared]
    )
    test_clang_relwithdebinfo_shared.depends_on(
        [build_clang_relwithdebinfo_all_tests_shared]
    )
    build_clang_release_all_shared.depends_on([configure_cmake_clang_shared])
    build_clang_release_all_tests_shared.depends_on([build_clang_release_all_shared])
    test_clang_release_shared.depends_on([build_clang_release_all_tests_shared])

    test_clang_debug_test_target_shared.depends_on([build_clang_debug_all_tests_shared])
    test_clang_relwithdebinfo_test_target_shared.depends_on(
        [build_clang_relwithdebinfo_all_tests_shared]
    )
    test_clang_release_test_target_shared.depends_on(
        [build_clang_release_all_tests_shared]
    )

    test_gcc_debug = Task("Test GCC Debug (static)", test_gcc_debug_fn)
    test_gcc_relwithdebinfo = Task(
        "Test GCC RelWithDebInfo (static)", test_gcc_relwithdebinfo_fn
    )
    test_gcc_release = Task("Test GCC Release (static)", test_gcc_release_fn)
    test_gcc_debug_test_target = Task(
        "Build GCC Debug test target (static)", test_gcc_debug_test_target_fn
    )
    test_gcc_relwithdebinfo_test_target = Task(
        "Build GCC RelWithDebInfo test target (static)",
        test_gcc_relwithdebinfo_test_target_fn,
    )
    test_gcc_release_test_target = Task(
        "Build GCC Release test target (static)", test_gcc_release_test_target_fn
    )
    build_gcc_debug_all = Task("Build GCC Debug (static; all)", build_gcc_debug_all_fn)
    build_gcc_debug_all_tests = Task(
        "Build GCC Debug (static; all_tests)", build_gcc_debug_all_tests_fn
    )
    build_gcc_relwithdebinfo_all = Task(
        "Build GCC RelWithDebInfo (static; all)", build_gcc_relwithdebinfo_all_fn
    )
    build_gcc_relwithdebinfo_all_tests = Task(
        "Build GCC RelWithDebInfo (static; all_tests)",
        build_gcc_relwithdebinfo_all_tests_fn,
    )
    build_gcc_release_all = Task(
        "Build GCC Release (static; all)", build_gcc_release_all_fn
    )
    build_gcc_release_all_tests = Task(
        "Build GCC Release (static; all_tests)", build_gcc_release_all_tests_fn
    )

    configure_cmake_gcc = Task(
        "Configure CMake for GCC (static)", configure_cmake_gcc_fn
    )

    test_gcc_debug_shared = Task("Test GCC Debug (dynamic)", test_gcc_debug_shared_fn)
    test_gcc_relwithdebinfo_shared = Task(
        "Test GCC RelWithDebInfo (dynamic)", test_gcc_relwithdebinfo_shared_fn
    )
    test_gcc_release_shared = Task(
        "Test GCC Release (dynamic)", test_gcc_release_shared_fn
    )
    test_gcc_debug_test_target_shared = Task(
        "Build GCC Debug test target (dynamic)", test_gcc_debug_test_target_shared_fn
    )
    test_gcc_relwithdebinfo_test_target_shared = Task(
        "Build GCC RelWithDebInfo test target (dynamic)",
        test_gcc_relwithdebinfo_test_target_shared_fn,
    )
    test_gcc_release_test_target_shared = Task(
        "Build GCC Release test target (dynamic)",
        test_gcc_release_test_target_shared_fn,
    )
    build_gcc_debug_all_shared = Task(
        "Build GCC Debug (dynamic; all)", build_gcc_debug_all_shared_fn
    )
    build_gcc_debug_all_tests_shared = Task(
        "Build GCC Debug (dynamic; all_tests)", build_gcc_debug_all_tests_shared_fn
    )
    build_gcc_relwithdebinfo_all_shared = Task(
        "Build GCC RelWithDebInfo (dynamic; all)",
        build_gcc_relwithdebinfo_all_shared_fn,
    )
    build_gcc_relwithdebinfo_all_tests_shared = Task(
        "Build GCC RelWithDebInfo (dynamic; all_tests)",
        build_gcc_relwithdebinfo_all_tests_shared_fn,
    )
    build_gcc_release_all_shared = Task(
        "Build GCC Release (dynamic; all)", build_gcc_release_all_shared_fn
    )
    build_gcc_release_all_tests_shared = Task(
        "Build GCC Release (dynamic; all_tests)", build_gcc_release_all_tests_shared_fn
    )

    configure_cmake_gcc_shared = Task(
        "Configure CMake for GCC (dynamic)", configure_cmake_gcc_shared_fn
    )

    build_gcc_debug_all.depends_on([configure_cmake_gcc])
    build_gcc_debug_all_tests.depends_on([build_gcc_debug_all])
    test_gcc_debug.depends_on([build_gcc_debug_all_tests])
    build_gcc_relwithdebinfo_all.depends_on([configure_cmake_gcc])
    build_gcc_relwithdebinfo_all_tests.depends_on([build_gcc_relwithdebinfo_all])
    test_gcc_relwithdebinfo.depends_on([build_gcc_relwithdebinfo_all_tests])
    build_gcc_release_all.depends_on([configure_cmake_gcc])
    build_gcc_release_all_tests.depends_on([build_gcc_release_all])
    test_gcc_release.depends_on([build_gcc_release_all_tests])

    test_gcc_debug_test_target.depends_on([build_gcc_debug_all_tests])
    test_gcc_relwithdebinfo_test_target.depends_on([build_gcc_relwithdebinfo_all_tests])
    test_gcc_release_test_target.depends_on([build_gcc_release_all_tests])

    build_gcc_debug_all_shared.depends_on([configure_cmake_gcc_shared])
    build_gcc_debug_all_tests_shared.depends_on([build_gcc_debug_all_shared])
    test_gcc_debug_shared.depends_on([build_gcc_debug_all_tests_shared])
    build_gcc_relwithdebinfo_all_shared.depends_on([configure_cmake_gcc_shared])
    build_gcc_relwithdebinfo_all_tests_shared.depends_on(
        [build_gcc_relwithdebinfo_all_shared]
    )
    test_gcc_relwithdebinfo_shared.depends_on(
        [build_gcc_relwithdebinfo_all_tests_shared]
    )
    build_gcc_release_all_shared.depends_on([configure_cmake_gcc_shared])
    build_gcc_release_all_tests_shared.depends_on([build_gcc_release_all_shared])
    test_gcc_release_shared.depends_on([build_gcc_release_all_tests_shared])

    test_gcc_debug_test_target_shared.depends_on([build_gcc_debug_all_tests_shared])
    test_gcc_relwithdebinfo_test_target_shared.depends_on(
        [build_gcc_relwithdebinfo_all_tests_shared]
    )
    test_gcc_release_test_target_shared.depends_on([build_gcc_release_all_tests_shared])

    install_gcc_debug = Task("Install GCC Debug (static)", install_gcc_debug_fn)
    install_gcc_relwithdebinfo = Task(
        "Install GCC RelWithDebInfo (static)", install_gcc_relwithdebinfo_fn
    )
    install_gcc_release = Task("Install GCC Release (static)", install_gcc_release_fn)
    install_clang_debug = Task("Install Clang Debug (static)", install_clang_debug_fn)
    install_clang_relwithdebinfo = Task(
        "Install Clang RelWithDebInfo (static)", install_clang_relwithdebinfo_fn
    )
    install_clang_release = Task(
        "Install Clang Release (static)", install_clang_release_fn
    )

    install_gcc_debug_shared = Task(
        "Install GCC Debug (dynamic)", install_gcc_debug_shared_fn
    )
    install_gcc_relwithdebinfo_shared = Task(
        "Install GCC RelWithDebInfo (dynamic)", install_gcc_relwithdebinfo_shared_fn
    )
    install_gcc_release_shared = Task(
        "Install GCC Release (dynamic)", install_gcc_release_shared_fn
    )
    install_clang_debug_shared = Task(
        "Install Clang Debug (dynamic)", install_clang_debug_shared_fn
    )
    install_clang_relwithdebinfo_shared = Task(
        "Install Clang RelWithDebInfo (dynamic)", install_clang_relwithdebinfo_shared_fn
    )
    install_clang_release_shared = Task(
        "Install Clang Release (dynamic)", install_clang_release_shared_fn
    )

    install_gcc_debug.depends_on([build_gcc_debug_all])
    install_gcc_relwithdebinfo.depends_on([build_gcc_relwithdebinfo_all])
    install_gcc_release.depends_on([build_gcc_release_all])
    install_clang_debug.depends_on([build_clang_debug_all])
    install_clang_relwithdebinfo.depends_on([build_clang_relwithdebinfo_all])
    install_clang_release.depends_on([build_clang_release_all])

    install_gcc_debug_shared.depends_on([build_gcc_debug_all_shared])
    install_gcc_relwithdebinfo_shared.depends_on([build_gcc_relwithdebinfo_all_shared])
    install_gcc_release_shared.depends_on([build_gcc_release_all_shared])
    install_clang_debug_shared.depends_on([build_clang_debug_all_shared])
    install_clang_relwithdebinfo_shared.depends_on(
        [build_clang_relwithdebinfo_all_shared]
    )
    install_clang_release_shared.depends_on([build_clang_release_all_shared])

    analyze_gcc_coverage = Task("Analyze GCC coverage data", analyze_gcc_coverage_fn)
    process_gcc_coverage = Task("Process GCC coverage data", process_coverage_fn)
    test_gcc_coverage = Task("Test GCC with coverage", test_gcc_coverage_fn)
    build_gcc_coverage_all = Task(
        "Build GCC with coverage (all)", build_gcc_coverage_all_fn
    )
    build_gcc_coverage_all_tests = Task(
        "Build GCC with coverage (all_tests)", build_gcc_coverage_all_tests_fn
    )
    configure_cmake_gcc_coverage = Task(
        "Configure CMake for GCC with coverage", configure_cmake_gcc_coverage_fn
    )

    analyze_gcc_coverage.depends_on([process_gcc_coverage])
    process_gcc_coverage.depends_on([test_gcc_coverage])
    test_gcc_coverage.depends_on([build_gcc_coverage_all_tests])
    build_gcc_coverage_all_tests.depends_on([build_gcc_coverage_all])
    build_gcc_coverage_all.depends_on([configure_cmake_gcc_coverage])

    configure_cmake_gcc_valgrind = Task("Configure CMake for GCC with Valgrind")
    configure_cmake_gcc_valgrind.depends_on([configure_cmake_gcc])
    build_gcc_valgrind = Task("Build GCC for Valgrind")
    build_gcc_valgrind.depends_on([build_gcc_debug_all, build_gcc_debug_all_tests])
    test_gcc_valgrind = Task("Test GCC build with Valgrind", test_gcc_valgrind_fn)
    test_gcc_valgrind.depends_on([build_gcc_valgrind])
    build_gcc_valgrind.depends_on([configure_cmake_gcc_valgrind])

    configure_cmake_clang_valgrind = Task("Configure CMake for Clang with Valgrind")
    configure_cmake_clang_valgrind.depends_on([configure_cmake_clang])
    build_clang_valgrind = Task("Build Clang for Valgrind")
    build_clang_valgrind.depends_on(
        [build_clang_debug_all, build_clang_debug_all_tests]
    )
    test_clang_valgrind = Task("Test Clang build with Valgrind", test_clang_valgrind_fn)
    test_clang_valgrind.depends_on([build_clang_valgrind])
    build_clang_valgrind.depends_on([configure_cmake_clang_valgrind])

    configure_cmake_clang_static_analysis = Task("Configure CMake for clang-tidy")
    configure_cmake_clang_static_analysis.depends_on([configure_cmake_clang])
    build_clang_static_analysis = Task("Build Clang for clang-tidy")
    build_clang_static_analysis.depends_on(
        [
            configure_cmake_clang_static_analysis,
            build_clang_debug_all,
            build_clang_debug_all_tests,
            build_clang_relwithdebinfo_all,
            build_clang_relwithdebinfo_all_tests,
            build_clang_release_all,
            build_clang_release_all_tests,
        ]
    )
    run_clang_static_analysis_all_files = Task(
        "Run clang-tidy", run_clang_static_analysis_all_files_fn
    )
    run_clang_static_analysis_changed_files = Task(
        "Run clang-tidy (incremental)", run_clang_static_analysis_changed_files_fn
    )

    misc_checks = Task("Miscellaneous checks", misc_checks_fn)
    verify_install_contents_static = Task(
        "Verify installation contents (static)", verify_install_contents_static_fn
    )
    verify_install_contents_static.depends_on(
        [
            install_clang_debug,
            install_clang_relwithdebinfo,
            install_clang_release,
            install_gcc_debug,
            install_gcc_relwithdebinfo,
            install_gcc_release,
        ]
    )
    verify_install_contents_shared = Task(
        "Verify installation contents (dynamic)", verify_install_contents_shared_fn
    )
    verify_install_contents_shared.depends_on(
        [
            install_clang_debug_shared,
            install_clang_relwithdebinfo_shared,
            install_clang_release_shared,
            install_gcc_debug_shared,
            install_gcc_relwithdebinfo_shared,
            install_gcc_release_shared,
        ]
    )

    check_license_file = Task("Check LICENSE file", check_license_file_fn)
    check_copyright_comments = Task(
        "Check copyright comments", check_copyright_comments_fn
    )
    check_formatting = Task("Check code formatting", check_formatting_fn)
    format_sources = Task("Format code", format_sources_fn)

    clean = Task("Clean build files", clean_fn)

    test_install_find_package_no_version_gcc_copy_artifacts = Task(
        "Copy GCC artifacts for test install (static; find_package, no version)",
        test_install_find_package_no_version_gcc_copy_artifacts_fn,
    )
    test_install_find_package_no_version_clang_copy_artifacts = Task(
        "Copy Clang artifacts for test install (static; find_package, no version)",
        test_install_find_package_no_version_clang_copy_artifacts_fn,
    )

    test_install_find_package_no_version_gcc_copy_artifacts.depends_on(
        [install_gcc_debug, install_gcc_relwithdebinfo, install_gcc_release]
    )
    test_install_find_package_no_version_clang_copy_artifacts.depends_on(
        [install_clang_debug, install_clang_relwithdebinfo, install_clang_release]
    )

    test_install_find_package_no_version_gcc_configure = Task(
        "Configure CMake for GCC test install (static; find_package, no version)",
        test_install_find_package_no_version_gcc_configure_fn,
    )
    test_install_find_package_no_version_clang_configure = Task(
        "Configure CMake for Clang test install (static; find_package, no version)",
        test_install_find_package_no_version_clang_configure_fn,
    )

    test_install_find_package_no_version_gcc_configure.depends_on(
        [test_install_find_package_no_version_gcc_copy_artifacts]
    )
    test_install_find_package_no_version_clang_configure.depends_on(
        [test_install_find_package_no_version_clang_copy_artifacts]
    )

    test_install_find_package_no_version_gcc_debug_build_all = Task(
        "Build GCC Debug test install (static; all; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_build_all_fn,
    )
    test_install_find_package_no_version_gcc_debug_build_all_tests = Task(
        "Build GCC Debug test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_build_all_tests_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all = Task(
        "Build GCC RelWithDebInfo test install (static; all; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_build_all_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests = Task(
        "Build GCC RelWithDebInfo test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_fn,
    )
    test_install_find_package_no_version_gcc_release_build_all = Task(
        "Build GCC Release test install (static; all; find_package, no version)",
        test_install_find_package_no_version_gcc_release_build_all_fn,
    )
    test_install_find_package_no_version_gcc_release_build_all_tests = Task(
        "Build GCC Release test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_release_build_all_tests_fn,
    )
    test_install_find_package_no_version_clang_debug_build_all = Task(
        "Build Clang Debug test install (static; all; find_package, no version)",
        test_install_find_package_no_version_clang_debug_build_all_fn,
    )
    test_install_find_package_no_version_clang_debug_build_all_tests = Task(
        "Build Clang Debug test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_debug_build_all_tests_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all = Task(
        "Build Clang RelWithDebInfo test install (static; all; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_build_all_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests = Task(
        "Build Clang RelWithDebInfo test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_fn,
    )
    test_install_find_package_no_version_clang_release_build_all = Task(
        "Build Clang Release test install (static; all; find_package, no version)",
        test_install_find_package_no_version_clang_release_build_all_fn,
    )
    test_install_find_package_no_version_clang_release_build_all_tests = Task(
        "Build Clang Release test install (static; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_release_build_all_tests_fn,
    )

    test_install_find_package_no_version_gcc_debug_test = Task(
        "Test GCC Debug test install (static; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_test_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_test = Task(
        "Test GCC RelWithDebInfo test install (static; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_test_fn,
    )
    test_install_find_package_no_version_gcc_release_test = Task(
        "Test GCC Release test install (static; find_package, no version)",
        test_install_find_package_no_version_gcc_release_test_fn,
    )
    test_install_find_package_no_version_clang_debug_test = Task(
        "Test Clang Debug test install (static; find_package, no version)",
        test_install_find_package_no_version_clang_debug_test_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_test = Task(
        "Test Clang RelWithDebInfo test install (static; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_test_fn,
    )
    test_install_find_package_no_version_clang_release_test = Task(
        "Test Clang Release test install (static; find_package, no version)",
        test_install_find_package_no_version_clang_release_test_fn,
    )

    test_install_find_package_no_version_gcc_debug_build_all.depends_on(
        [test_install_find_package_no_version_gcc_configure]
    )
    test_install_find_package_no_version_gcc_debug_build_all_tests.depends_on(
        [test_install_find_package_no_version_gcc_debug_build_all]
    )
    test_install_find_package_no_version_gcc_debug_test.depends_on(
        [test_install_find_package_no_version_gcc_debug_build_all_tests]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all.depends_on(
        [test_install_find_package_no_version_gcc_configure]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests.depends_on(
        [test_install_find_package_no_version_gcc_relwithdebinfo_build_all]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_test.depends_on(
        [test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests]
    )
    test_install_find_package_no_version_gcc_release_build_all.depends_on(
        [test_install_find_package_no_version_gcc_configure]
    )
    test_install_find_package_no_version_gcc_release_build_all_tests.depends_on(
        [test_install_find_package_no_version_gcc_release_build_all]
    )
    test_install_find_package_no_version_gcc_release_test.depends_on(
        [test_install_find_package_no_version_gcc_release_build_all_tests]
    )
    test_install_find_package_no_version_clang_debug_build_all.depends_on(
        [test_install_find_package_no_version_clang_configure]
    )
    test_install_find_package_no_version_clang_debug_build_all_tests.depends_on(
        [test_install_find_package_no_version_clang_debug_build_all]
    )
    test_install_find_package_no_version_clang_debug_test.depends_on(
        [test_install_find_package_no_version_clang_debug_build_all_tests]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all.depends_on(
        [test_install_find_package_no_version_clang_configure]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests.depends_on(
        [test_install_find_package_no_version_clang_relwithdebinfo_build_all]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_test.depends_on(
        [test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests]
    )
    test_install_find_package_no_version_clang_release_build_all.depends_on(
        [test_install_find_package_no_version_clang_configure]
    )
    test_install_find_package_no_version_clang_release_build_all_tests.depends_on(
        [test_install_find_package_no_version_clang_release_build_all]
    )
    test_install_find_package_no_version_clang_release_test.depends_on(
        [test_install_find_package_no_version_clang_release_build_all_tests]
    )

    test_install_find_package_exact_version_gcc_copy_artifacts = Task(
        "Copy GCC artifacts for test install (static; find_package, exact version)",
        test_install_find_package_exact_version_gcc_copy_artifacts_fn,
    )
    test_install_find_package_exact_version_clang_copy_artifacts = Task(
        "Copy Clang artifacts for test install (static; find_package, exact version)",
        test_install_find_package_exact_version_clang_copy_artifacts_fn,
    )

    test_install_find_package_exact_version_gcc_copy_artifacts.depends_on(
        [install_gcc_debug, install_gcc_relwithdebinfo, install_gcc_release]
    )
    test_install_find_package_exact_version_clang_copy_artifacts.depends_on(
        [install_clang_debug, install_clang_relwithdebinfo, install_clang_release]
    )

    test_install_find_package_exact_version_gcc_configure = Task(
        "Configure CMake for GCC test install (static; find_package, exact version)",
        test_install_find_package_exact_version_gcc_configure_fn,
    )
    test_install_find_package_exact_version_clang_configure = Task(
        "Configure CMake for Clang test install (static; find_package, exact version)",
        test_install_find_package_exact_version_clang_configure_fn,
    )

    test_install_find_package_exact_version_gcc_configure.depends_on(
        [test_install_find_package_exact_version_gcc_copy_artifacts]
    )
    test_install_find_package_exact_version_clang_configure.depends_on(
        [test_install_find_package_exact_version_clang_copy_artifacts]
    )

    test_install_find_package_exact_version_gcc_debug_build_all = Task(
        "Build GCC Debug test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_build_all_fn,
    )
    test_install_find_package_exact_version_gcc_debug_build_all_tests = Task(
        "Build GCC Debug test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_build_all_tests_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all = Task(
        "Build GCC RelWithDebInfo test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests = Task(
        "Build GCC RelWithDebInfo test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_fn,
    )
    test_install_find_package_exact_version_gcc_release_build_all = Task(
        "Build GCC Release test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_build_all_fn,
    )
    test_install_find_package_exact_version_gcc_release_build_all_tests = Task(
        "Build GCC Release test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_build_all_tests_fn,
    )
    test_install_find_package_exact_version_clang_debug_build_all = Task(
        "Build Clang Debug test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_build_all_fn,
    )
    test_install_find_package_exact_version_clang_debug_build_all_tests = Task(
        "Build Clang Debug test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_build_all_tests_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all = Task(
        "Build Clang RelWithDebInfo test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_build_all_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests = Task(
        "Build Clang RelWithDebInfo test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_fn,
    )
    test_install_find_package_exact_version_clang_release_build_all = Task(
        "Build Clang Release test install (static; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_build_all_fn,
    )
    test_install_find_package_exact_version_clang_release_build_all_tests = Task(
        "Build Clang Release test install (static; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_build_all_tests_fn,
    )

    test_install_find_package_exact_version_gcc_debug_test = Task(
        "Test GCC Debug test install (static; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_test_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_test = Task(
        "Test GCC RelWithDebInfo test install (static; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_test_fn,
    )
    test_install_find_package_exact_version_gcc_release_test = Task(
        "Test GCC Release test install (static; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_test_fn,
    )
    test_install_find_package_exact_version_clang_debug_test = Task(
        "Test Clang Debug test install (static; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_test_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_test = Task(
        "Test Clang RelWithDebInfo test install (static; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_test_fn,
    )
    test_install_find_package_exact_version_clang_release_test = Task(
        "Test Clang Release test install (static; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_test_fn,
    )

    test_install_find_package_exact_version_gcc_debug_build_all.depends_on(
        [test_install_find_package_exact_version_gcc_configure]
    )
    test_install_find_package_exact_version_gcc_debug_build_all_tests.depends_on(
        [test_install_find_package_exact_version_gcc_debug_build_all]
    )
    test_install_find_package_exact_version_gcc_debug_test.depends_on(
        [test_install_find_package_exact_version_gcc_debug_build_all_tests]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all.depends_on(
        [test_install_find_package_exact_version_gcc_configure]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests.depends_on(
        [test_install_find_package_exact_version_gcc_relwithdebinfo_build_all]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_test.depends_on(
        [test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests]
    )
    test_install_find_package_exact_version_gcc_release_build_all.depends_on(
        [test_install_find_package_exact_version_gcc_configure]
    )
    test_install_find_package_exact_version_gcc_release_build_all_tests.depends_on(
        [test_install_find_package_exact_version_gcc_release_build_all]
    )
    test_install_find_package_exact_version_gcc_release_test.depends_on(
        [test_install_find_package_exact_version_gcc_release_build_all_tests]
    )
    test_install_find_package_exact_version_clang_debug_build_all.depends_on(
        [test_install_find_package_exact_version_clang_configure]
    )
    test_install_find_package_exact_version_clang_debug_build_all_tests.depends_on(
        [test_install_find_package_exact_version_clang_debug_build_all]
    )
    test_install_find_package_exact_version_clang_debug_test.depends_on(
        [test_install_find_package_exact_version_clang_debug_build_all_tests]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all.depends_on(
        [test_install_find_package_exact_version_clang_configure]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests.depends_on(
        [test_install_find_package_exact_version_clang_relwithdebinfo_build_all]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_test.depends_on(
        [test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests]
    )
    test_install_find_package_exact_version_clang_release_build_all.depends_on(
        [test_install_find_package_exact_version_clang_configure]
    )
    test_install_find_package_exact_version_clang_release_build_all_tests.depends_on(
        [test_install_find_package_exact_version_clang_release_build_all]
    )
    test_install_find_package_exact_version_clang_release_test.depends_on(
        [test_install_find_package_exact_version_clang_release_build_all_tests]
    )

    test_install_find_package_no_version_gcc_copy_artifacts_shared = Task(
        "Copy GCC artifacts for test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_gcc_copy_artifacts_shared_fn,
    )
    test_install_find_package_no_version_clang_copy_artifacts_shared = Task(
        "Copy Clang artifacts for test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_clang_copy_artifacts_shared_fn,
    )

    test_install_find_package_no_version_gcc_copy_artifacts_shared.depends_on(
        [
            install_gcc_debug_shared,
            install_gcc_relwithdebinfo_shared,
            install_gcc_release_shared,
        ]
    )
    test_install_find_package_no_version_clang_copy_artifacts_shared.depends_on(
        [
            install_clang_debug_shared,
            install_clang_relwithdebinfo_shared,
            install_clang_release_shared,
        ]
    )

    test_install_find_package_no_version_gcc_configure_shared = Task(
        "Configure CMake for GCC test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_gcc_configure_shared_fn,
    )
    test_install_find_package_no_version_clang_configure_shared = Task(
        "Configure CMake for Clang test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_clang_configure_shared_fn,
    )

    test_install_find_package_no_version_gcc_configure_shared.depends_on(
        [test_install_find_package_no_version_gcc_copy_artifacts_shared]
    )
    test_install_find_package_no_version_clang_configure_shared.depends_on(
        [test_install_find_package_no_version_clang_copy_artifacts_shared]
    )

    test_install_find_package_no_version_gcc_debug_build_all_shared = Task(
        "Build GCC Debug test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_build_all_shared_fn,
    )
    test_install_find_package_no_version_gcc_debug_build_all_tests_shared = Task(
        "Build GCC Debug test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_build_all_tests_shared_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_find_package_no_version_gcc_release_build_all_shared = Task(
        "Build GCC Release test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_gcc_release_build_all_shared_fn,
    )
    test_install_find_package_no_version_gcc_release_build_all_tests_shared = Task(
        "Build GCC Release test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_gcc_release_build_all_tests_shared_fn,
    )
    test_install_find_package_no_version_clang_debug_build_all_shared = Task(
        "Build Clang Debug test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_clang_debug_build_all_shared_fn,
    )
    test_install_find_package_no_version_clang_debug_build_all_tests_shared = Task(
        "Build Clang Debug test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_debug_build_all_tests_shared_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_find_package_no_version_clang_release_build_all_shared = Task(
        "Build Clang Release test install (dynamic; all; find_package, no version)",
        test_install_find_package_no_version_clang_release_build_all_shared_fn,
    )
    test_install_find_package_no_version_clang_release_build_all_tests_shared = Task(
        "Build Clang Release test install (dynamic; all_tests; find_package, no version)",
        test_install_find_package_no_version_clang_release_build_all_tests_shared_fn,
    )

    test_install_find_package_no_version_gcc_debug_test_shared = Task(
        "Test GCC Debug test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_gcc_debug_test_shared_fn,
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_test_shared = Task(
        "Test GCC RelWithDebInfo test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_gcc_relwithdebinfo_test_shared_fn,
    )
    test_install_find_package_no_version_gcc_release_test_shared = Task(
        "Test GCC Release test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_gcc_release_test_shared_fn,
    )
    test_install_find_package_no_version_clang_debug_test_shared = Task(
        "Test Clang Debug test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_clang_debug_test_shared_fn,
    )
    test_install_find_package_no_version_clang_relwithdebinfo_test_shared = Task(
        "Test Clang RelWithDebInfo test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_clang_relwithdebinfo_test_shared_fn,
    )
    test_install_find_package_no_version_clang_release_test_shared = Task(
        "Test Clang Release test install (dynamic; find_package, no version)",
        test_install_find_package_no_version_clang_release_test_shared_fn,
    )

    test_install_find_package_no_version_gcc_debug_build_all_shared.depends_on(
        [test_install_find_package_no_version_gcc_configure_shared]
    )
    test_install_find_package_no_version_gcc_debug_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_gcc_debug_build_all_shared]
    )
    test_install_find_package_no_version_gcc_debug_test_shared.depends_on(
        [test_install_find_package_no_version_gcc_debug_build_all_tests_shared]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared.depends_on(
        [test_install_find_package_no_version_gcc_configure_shared]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared]
    )
    test_install_find_package_no_version_gcc_relwithdebinfo_test_shared.depends_on(
        [test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared]
    )
    test_install_find_package_no_version_gcc_release_build_all_shared.depends_on(
        [test_install_find_package_no_version_gcc_configure_shared]
    )
    test_install_find_package_no_version_gcc_release_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_gcc_release_build_all_shared]
    )
    test_install_find_package_no_version_gcc_release_test_shared.depends_on(
        [test_install_find_package_no_version_gcc_release_build_all_tests_shared]
    )
    test_install_find_package_no_version_clang_debug_build_all_shared.depends_on(
        [test_install_find_package_no_version_clang_configure_shared]
    )
    test_install_find_package_no_version_clang_debug_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_clang_debug_build_all_shared]
    )
    test_install_find_package_no_version_clang_debug_test_shared.depends_on(
        [test_install_find_package_no_version_clang_debug_build_all_tests_shared]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared.depends_on(
        [test_install_find_package_no_version_clang_configure_shared]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared]
    )
    test_install_find_package_no_version_clang_relwithdebinfo_test_shared.depends_on(
        [
            test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared
        ]
    )
    test_install_find_package_no_version_clang_release_build_all_shared.depends_on(
        [test_install_find_package_no_version_clang_configure_shared]
    )
    test_install_find_package_no_version_clang_release_build_all_tests_shared.depends_on(
        [test_install_find_package_no_version_clang_release_build_all_shared]
    )
    test_install_find_package_no_version_clang_release_test_shared.depends_on(
        [test_install_find_package_no_version_clang_release_build_all_tests_shared]
    )

    test_install_find_package_exact_version_gcc_copy_artifacts_shared = Task(
        "Copy GCC artifacts for test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_gcc_copy_artifacts_shared_fn,
    )
    test_install_find_package_exact_version_clang_copy_artifacts_shared = Task(
        "Copy Clang artifacts for test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_clang_copy_artifacts_shared_fn,
    )

    test_install_find_package_exact_version_gcc_copy_artifacts_shared.depends_on(
        [
            install_gcc_debug_shared,
            install_gcc_relwithdebinfo_shared,
            install_gcc_release_shared,
        ]
    )
    test_install_find_package_exact_version_clang_copy_artifacts_shared.depends_on(
        [
            install_clang_debug_shared,
            install_clang_relwithdebinfo_shared,
            install_clang_release_shared,
        ]
    )

    test_install_find_package_exact_version_gcc_configure_shared = Task(
        "Configure CMake for GCC test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_gcc_configure_shared_fn,
    )
    test_install_find_package_exact_version_clang_configure_shared = Task(
        "Configure CMake for Clang test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_clang_configure_shared_fn,
    )

    test_install_find_package_exact_version_gcc_configure_shared.depends_on(
        [test_install_find_package_exact_version_gcc_copy_artifacts_shared]
    )
    test_install_find_package_exact_version_clang_configure_shared.depends_on(
        [test_install_find_package_exact_version_clang_copy_artifacts_shared]
    )

    test_install_find_package_exact_version_gcc_debug_build_all_shared = Task(
        "Build GCC Debug test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_build_all_shared_fn,
    )
    test_install_find_package_exact_version_gcc_debug_build_all_tests_shared = Task(
        "Build GCC Debug test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_build_all_tests_shared_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_find_package_exact_version_gcc_release_build_all_shared = Task(
        "Build GCC Release test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_build_all_shared_fn,
    )
    test_install_find_package_exact_version_gcc_release_build_all_tests_shared = Task(
        "Build GCC Release test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_build_all_tests_shared_fn,
    )
    test_install_find_package_exact_version_clang_debug_build_all_shared = Task(
        "Build Clang Debug test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_build_all_shared_fn,
    )
    test_install_find_package_exact_version_clang_debug_build_all_tests_shared = Task(
        "Build Clang Debug test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_build_all_tests_shared_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_find_package_exact_version_clang_release_build_all_shared = Task(
        "Build Clang Release test install (dynamic; all; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_build_all_shared_fn,
    )
    test_install_find_package_exact_version_clang_release_build_all_tests_shared = Task(
        "Build Clang Release test install (dynamic; all_tests; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_build_all_tests_shared_fn,
    )

    test_install_find_package_exact_version_gcc_debug_test_shared = Task(
        "Test GCC Debug test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_gcc_debug_test_shared_fn,
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared = Task(
        "Test GCC RelWithDebInfo test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared_fn,
    )
    test_install_find_package_exact_version_gcc_release_test_shared = Task(
        "Test GCC Release test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_gcc_release_test_shared_fn,
    )
    test_install_find_package_exact_version_clang_debug_test_shared = Task(
        "Test Clang Debug test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_clang_debug_test_shared_fn,
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_test_shared = Task(
        "Test Clang RelWithDebInfo test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_clang_relwithdebinfo_test_shared_fn,
    )
    test_install_find_package_exact_version_clang_release_test_shared = Task(
        "Test Clang Release test install (dynamic; find_package, exact version)",
        test_install_find_package_exact_version_clang_release_test_shared_fn,
    )

    test_install_find_package_exact_version_gcc_debug_build_all_shared.depends_on(
        [test_install_find_package_exact_version_gcc_configure_shared]
    )
    test_install_find_package_exact_version_gcc_debug_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_gcc_debug_build_all_shared]
    )
    test_install_find_package_exact_version_gcc_debug_test_shared.depends_on(
        [test_install_find_package_exact_version_gcc_debug_build_all_tests_shared]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared.depends_on(
        [test_install_find_package_exact_version_gcc_configure_shared]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared]
    )
    test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared.depends_on(
        [
            test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared
        ]
    )
    test_install_find_package_exact_version_gcc_release_build_all_shared.depends_on(
        [test_install_find_package_exact_version_gcc_configure_shared]
    )
    test_install_find_package_exact_version_gcc_release_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_gcc_release_build_all_shared]
    )
    test_install_find_package_exact_version_gcc_release_test_shared.depends_on(
        [test_install_find_package_exact_version_gcc_release_build_all_tests_shared]
    )
    test_install_find_package_exact_version_clang_debug_build_all_shared.depends_on(
        [test_install_find_package_exact_version_clang_configure_shared]
    )
    test_install_find_package_exact_version_clang_debug_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_clang_debug_build_all_shared]
    )
    test_install_find_package_exact_version_clang_debug_test_shared.depends_on(
        [test_install_find_package_exact_version_clang_debug_build_all_tests_shared]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared.depends_on(
        [test_install_find_package_exact_version_clang_configure_shared]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared]
    )
    test_install_find_package_exact_version_clang_relwithdebinfo_test_shared.depends_on(
        [
            test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared
        ]
    )
    test_install_find_package_exact_version_clang_release_build_all_shared.depends_on(
        [test_install_find_package_exact_version_clang_configure_shared]
    )
    test_install_find_package_exact_version_clang_release_build_all_tests_shared.depends_on(
        [test_install_find_package_exact_version_clang_release_build_all_shared]
    )
    test_install_find_package_exact_version_clang_release_test_shared.depends_on(
        [test_install_find_package_exact_version_clang_release_build_all_tests_shared]
    )

    test_install_test_install_add_subdirectory_copy_sources = Task(
        "Copy sources for test install (add_subdirectory)",
        test_install_add_subdirectory_copy_sources_fn,
    )

    test_install_add_subdirectory_gcc_configure = Task(
        "Configure CMake for GCC test install (static; add_subdirectory)",
        test_install_add_subdirectory_gcc_configure_fn,
    )
    test_install_add_subdirectory_clang_configure = Task(
        "Configure CMake for Clang test install (static; add_subdirectory)",
        test_install_add_subdirectory_clang_configure_fn,
    )

    test_install_add_subdirectory_gcc_configure.depends_on(
        [test_install_test_install_add_subdirectory_copy_sources]
    )
    test_install_add_subdirectory_clang_configure.depends_on(
        [test_install_test_install_add_subdirectory_copy_sources]
    )

    test_install_add_subdirectory_gcc_debug_build_all = Task(
        "Build GCC Debug test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_build_all_fn,
    )
    test_install_add_subdirectory_gcc_debug_build_all_tests = Task(
        "Build GCC Debug test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_build_all_tests_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all = Task(
        "Build GCC RelWithDebInfo test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_build_all_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests = Task(
        "Build GCC RelWithDebInfo test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_fn,
    )
    test_install_add_subdirectory_gcc_release_build_all = Task(
        "Build GCC Release test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_build_all_fn,
    )
    test_install_add_subdirectory_gcc_release_build_all_tests = Task(
        "Build GCC Release test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_build_all_tests_fn,
    )
    test_install_add_subdirectory_clang_debug_build_all = Task(
        "Build Clang Debug test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_build_all_fn,
    )
    test_install_add_subdirectory_clang_debug_build_all_tests = Task(
        "Build Clang Debug test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_build_all_tests_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all = Task(
        "Build Clang RelWithDebInfo test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_build_all_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests = Task(
        "Build Clang RelWithDebInfo test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_fn,
    )
    test_install_add_subdirectory_clang_release_build_all = Task(
        "Build Clang Release test install (static; all; add_subdirectory)",
        test_install_add_subdirectory_clang_release_build_all_fn,
    )
    test_install_add_subdirectory_clang_release_build_all_tests = Task(
        "Build Clang Release test install (static; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_release_build_all_tests_fn,
    )

    test_install_add_subdirectory_gcc_debug_test = Task(
        "Test GCC Debug test install (static; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_test_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_test = Task(
        "Test GCC RelWithDebInfo test install (static; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_test_fn,
    )
    test_install_add_subdirectory_gcc_release_test = Task(
        "Test GCC Release test install (static; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_test_fn,
    )
    test_install_add_subdirectory_clang_debug_test = Task(
        "Test Clang Debug test install (static; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_test_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_test = Task(
        "Test Clang RelWithDebInfo test install (static; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_test_fn,
    )
    test_install_add_subdirectory_clang_release_test = Task(
        "Test Clang Release test install (static; add_subdirectory)",
        test_install_add_subdirectory_clang_release_test_fn,
    )

    test_install_add_subdirectory_gcc_debug_build_all.depends_on(
        [test_install_add_subdirectory_gcc_configure]
    )
    test_install_add_subdirectory_gcc_debug_build_all_tests.depends_on(
        [test_install_add_subdirectory_gcc_debug_build_all]
    )
    test_install_add_subdirectory_gcc_debug_test.depends_on(
        [test_install_add_subdirectory_gcc_debug_build_all_tests]
    )

    test_install_add_subdirectory_gcc_relwithdebinfo_build_all.depends_on(
        [test_install_add_subdirectory_gcc_configure]
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests.depends_on(
        [test_install_add_subdirectory_gcc_relwithdebinfo_build_all]
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_test.depends_on(
        [test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests]
    )
    test_install_add_subdirectory_gcc_release_build_all.depends_on(
        [test_install_add_subdirectory_gcc_configure]
    )
    test_install_add_subdirectory_gcc_release_build_all_tests.depends_on(
        [test_install_add_subdirectory_gcc_release_build_all]
    )
    test_install_add_subdirectory_gcc_release_test.depends_on(
        [test_install_add_subdirectory_gcc_release_build_all_tests]
    )
    test_install_add_subdirectory_clang_debug_build_all.depends_on(
        [test_install_add_subdirectory_clang_configure]
    )
    test_install_add_subdirectory_clang_debug_build_all_tests.depends_on(
        [test_install_add_subdirectory_clang_debug_build_all]
    )
    test_install_add_subdirectory_clang_debug_test.depends_on(
        [test_install_add_subdirectory_clang_debug_build_all_tests]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all.depends_on(
        [test_install_add_subdirectory_clang_configure]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests.depends_on(
        [test_install_add_subdirectory_clang_relwithdebinfo_build_all]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_test.depends_on(
        [test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests]
    )
    test_install_add_subdirectory_clang_release_build_all.depends_on(
        [test_install_add_subdirectory_clang_configure]
    )
    test_install_add_subdirectory_clang_release_build_all_tests.depends_on(
        [test_install_add_subdirectory_clang_release_build_all]
    )
    test_install_add_subdirectory_clang_release_test.depends_on(
        [test_install_add_subdirectory_clang_release_build_all_tests]
    )

    test_install_add_subdirectory_gcc_configure_shared = Task(
        "Configure CMake for GCC test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_gcc_configure_shared_fn,
    )
    test_install_add_subdirectory_clang_configure_shared = Task(
        "Configure CMake for Clang test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_clang_configure_shared_fn,
    )

    test_install_add_subdirectory_gcc_configure_shared.depends_on(
        [test_install_test_install_add_subdirectory_copy_sources]
    )
    test_install_add_subdirectory_clang_configure_shared.depends_on(
        [test_install_test_install_add_subdirectory_copy_sources]
    )

    test_install_add_subdirectory_gcc_debug_build_all_shared = Task(
        "Build GCC Debug test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_build_all_shared_fn,
    )
    test_install_add_subdirectory_gcc_debug_build_all_tests_shared = Task(
        "Build GCC Debug test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_build_all_tests_shared_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared = Task(
        "Build GCC RelWithDebInfo test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_add_subdirectory_gcc_release_build_all_shared = Task(
        "Build GCC Release test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_build_all_shared_fn,
    )
    test_install_add_subdirectory_gcc_release_build_all_tests_shared = Task(
        "Build GCC Release test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_build_all_tests_shared_fn,
    )
    test_install_add_subdirectory_clang_debug_build_all_shared = Task(
        "Build Clang Debug test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_build_all_shared_fn,
    )
    test_install_add_subdirectory_clang_debug_build_all_tests_shared = Task(
        "Build Clang Debug test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_build_all_tests_shared_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared = Task(
        "Build Clang RelWithDebInfo test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared_fn,
    )
    test_install_add_subdirectory_clang_release_build_all_shared = Task(
        "Build Clang Release test install (dynamic; all; add_subdirectory)",
        test_install_add_subdirectory_clang_release_build_all_shared_fn,
    )
    test_install_add_subdirectory_clang_release_build_all_tests_shared = Task(
        "Build Clang Release test install (dynamic; all_tests; add_subdirectory)",
        test_install_add_subdirectory_clang_release_build_all_tests_shared_fn,
    )

    test_install_add_subdirectory_gcc_debug_test_shared = Task(
        "Test GCC Debug test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_gcc_debug_test_shared_fn,
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_test_shared = Task(
        "Test GCC RelWithDebInfo test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_gcc_relwithdebinfo_test_shared_fn,
    )
    test_install_add_subdirectory_gcc_release_test_shared = Task(
        "Test GCC Release test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_gcc_release_test_shared_fn,
    )
    test_install_add_subdirectory_clang_debug_test_shared = Task(
        "Test Clang Debug test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_clang_debug_test_shared_fn,
    )
    test_install_add_subdirectory_clang_relwithdebinfo_test_shared = Task(
        "Test Clang RelWithDebInfo test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_clang_relwithdebinfo_test_shared_fn,
    )
    test_install_add_subdirectory_clang_release_test_shared = Task(
        "Test Clang Release test install (dynamic; add_subdirectory)",
        test_install_add_subdirectory_clang_release_test_shared_fn,
    )

    test_install_add_subdirectory_gcc_debug_build_all_shared.depends_on(
        [test_install_add_subdirectory_gcc_configure_shared]
    )
    test_install_add_subdirectory_gcc_debug_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_gcc_debug_build_all_shared]
    )
    test_install_add_subdirectory_gcc_debug_test_shared.depends_on(
        [test_install_add_subdirectory_gcc_debug_build_all_tests_shared]
    )

    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared.depends_on(
        [test_install_add_subdirectory_gcc_configure_shared]
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared]
    )
    test_install_add_subdirectory_gcc_relwithdebinfo_test_shared.depends_on(
        [test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared]
    )
    test_install_add_subdirectory_gcc_release_build_all_shared.depends_on(
        [test_install_add_subdirectory_gcc_configure_shared]
    )
    test_install_add_subdirectory_gcc_release_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_gcc_release_build_all_shared]
    )
    test_install_add_subdirectory_gcc_release_test_shared.depends_on(
        [test_install_add_subdirectory_gcc_release_build_all_tests_shared]
    )
    test_install_add_subdirectory_clang_debug_build_all_shared.depends_on(
        [test_install_add_subdirectory_clang_configure_shared]
    )
    test_install_add_subdirectory_clang_debug_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_clang_debug_build_all_shared]
    )
    test_install_add_subdirectory_clang_debug_test_shared.depends_on(
        [test_install_add_subdirectory_clang_debug_build_all_tests_shared]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared.depends_on(
        [test_install_add_subdirectory_clang_configure_shared]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared]
    )
    test_install_add_subdirectory_clang_relwithdebinfo_test_shared.depends_on(
        [test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared]
    )
    test_install_add_subdirectory_clang_release_build_all_shared.depends_on(
        [test_install_add_subdirectory_clang_configure_shared]
    )
    test_install_add_subdirectory_clang_release_build_all_tests_shared.depends_on(
        [test_install_add_subdirectory_clang_release_build_all_shared]
    )
    test_install_add_subdirectory_clang_release_test_shared.depends_on(
        [test_install_add_subdirectory_clang_release_build_all_tests_shared]
    )

    configure_example_clang = Task(
        "Configure example Clang (static)", configure_example_clang_fn
    )
    build_example_clang_debug_all = Task(
        "Build example Clang Debug (static)", build_example_clang_debug_all_fn
    )
    build_example_clang_relwithdebinfo_all = Task(
        "Build example Clang RelWithDebInfo (static)",
        build_example_clang_relwithdebinfo_all_fn,
    )
    build_example_clang_release_all = Task(
        "Build example Clang Release (static)", build_example_clang_release_all_fn
    )
    install_example_clang_debug = Task(
        "Install example Clang Debug (static)", install_example_clang_debug_fn
    )
    install_example_clang_relwithdebinfo = Task(
        "Install example Clang RelWithDebInfo (static)",
        install_example_clang_relwithdebinfo_fn,
    )
    install_example_clang_release = Task(
        "Install example Clang Release (static)", install_example_clang_release_fn
    )
    configure_example_clang_shared = Task(
        "Configure example Clang (dynamic)", configure_example_clang_shared_fn
    )
    build_example_clang_debug_all_shared = Task(
        "Build example Clang Debug (dynamic)", build_example_clang_debug_all_shared_fn
    )
    build_example_clang_relwithdebinfo_all_shared = Task(
        "Build example Clang RelWithDebInfo (dynamic)",
        build_example_clang_relwithdebinfo_all_shared_fn,
    )
    build_example_clang_release_all_shared = Task(
        "Build example Clang Release (dynamic)",
        build_example_clang_release_all_shared_fn,
    )
    install_example_clang_debug_shared = Task(
        "Install example Clang Debug (dynamic)", install_example_clang_debug_shared_fn
    )
    install_example_clang_relwithdebinfo_shared = Task(
        "Install example Clang RelWithDebInfo (dynamic)",
        install_example_clang_relwithdebinfo_shared_fn,
    )
    install_example_clang_release_shared = Task(
        "Install example Clang Release (dynamic)",
        install_example_clang_release_shared_fn,
    )
    build_example_clang_debug_all.depends_on([configure_example_clang])
    build_example_clang_relwithdebinfo_all.depends_on([configure_example_clang])
    build_example_clang_release_all.depends_on([configure_example_clang])
    build_example_clang_debug_all_shared.depends_on([configure_example_clang_shared])
    build_example_clang_relwithdebinfo_all_shared.depends_on(
        [configure_example_clang_shared]
    )
    build_example_clang_release_all_shared.depends_on([configure_example_clang_shared])
    install_example_clang_debug.depends_on([build_example_clang_debug_all])
    install_example_clang_relwithdebinfo.depends_on(
        [build_example_clang_relwithdebinfo_all]
    )
    install_example_clang_release.depends_on([build_example_clang_release_all])
    install_example_clang_debug_shared.depends_on(
        [build_example_clang_debug_all_shared]
    )
    install_example_clang_relwithdebinfo_shared.depends_on(
        [build_example_clang_relwithdebinfo_all_shared]
    )
    install_example_clang_release_shared.depends_on(
        [build_example_clang_release_all_shared]
    )
    example_quick_start_build_and_install = Task(
        "Test examples/quick_start_build_and_install",
        example_quick_start_build_and_install_fn,
    )
    example_quick_start_build_and_install.depends_on(
        [
            install_example_clang_debug,
            install_example_clang_relwithdebinfo,
            install_example_clang_release,
            install_example_clang_debug_shared,
            install_example_clang_relwithdebinfo_shared,
            install_example_clang_release_shared,
        ]
    )

    example_quick_start_add_subdirectory = Task(
        "Test examples/quick_start_add_subdirectory",
        example_quick_start_add_subdirectory_fn,
    )

    run_clang_static_analysis_all_files.depends_on(
        [
            build_clang_static_analysis,
            test_install_find_package_no_version_clang_debug_build_all,
            test_install_find_package_no_version_clang_debug_build_all_tests,
            test_install_find_package_no_version_clang_relwithdebinfo_build_all,
            test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests,
            test_install_find_package_no_version_clang_release_build_all,
            test_install_find_package_no_version_clang_release_build_all_tests,
            test_install_find_package_exact_version_clang_debug_build_all,
            test_install_find_package_exact_version_clang_debug_build_all_tests,
            test_install_find_package_exact_version_clang_relwithdebinfo_build_all,
            test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests,
            test_install_find_package_exact_version_clang_release_build_all,
            test_install_find_package_exact_version_clang_release_build_all_tests,
            test_install_add_subdirectory_clang_debug_build_all,
            test_install_add_subdirectory_clang_debug_build_all_tests,
            test_install_add_subdirectory_clang_relwithdebinfo_build_all,
            test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests,
            test_install_add_subdirectory_clang_release_build_all,
            test_install_add_subdirectory_clang_release_build_all_tests,
            example_quick_start_build_and_install,
            example_quick_start_add_subdirectory,
        ]
    )
    run_clang_static_analysis_changed_files.depends_on(
        [
            build_clang_static_analysis,
            test_install_find_package_no_version_clang_debug_build_all,
            test_install_find_package_no_version_clang_debug_build_all_tests,
            test_install_find_package_no_version_clang_relwithdebinfo_build_all,
            test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests,
            test_install_find_package_no_version_clang_release_build_all,
            test_install_find_package_no_version_clang_release_build_all_tests,
            test_install_find_package_exact_version_clang_debug_build_all,
            test_install_find_package_exact_version_clang_debug_build_all_tests,
            test_install_find_package_exact_version_clang_relwithdebinfo_build_all,
            test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests,
            test_install_find_package_exact_version_clang_release_build_all,
            test_install_find_package_exact_version_clang_release_build_all_tests,
            test_install_add_subdirectory_clang_debug_build_all,
            test_install_add_subdirectory_clang_debug_build_all_tests,
            test_install_add_subdirectory_clang_relwithdebinfo_build_all,
            test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests,
            test_install_add_subdirectory_clang_release_build_all,
            test_install_add_subdirectory_clang_release_build_all_tests,
            example_quick_start_build_and_install,
            example_quick_start_add_subdirectory,
        ]
    )

    prebuild_dependencies = []
    build_dependencies = []

    if mode.clean:
        prebuild_dependencies.append(clean)

    if mode.check_legal:
        build_dependencies.append(check_license_file)
        build_dependencies.append(check_copyright_comments)

    if mode.check_formatting:
        build_dependencies.append(check_formatting)

    if mode.fix_formatting:
        build_dependencies.append(format_sources)

    if mode.misc:
        build_dependencies.append(misc_checks)

    if mode.gcc:
        if mode.debug:
            if mode.static_lib:
                build_dependencies.append(build_gcc_debug_all)
            if mode.shared_lib:
                build_dependencies.append(build_gcc_debug_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_debug)
                if mode.shared_lib:
                    build_dependencies.append(test_gcc_debug_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_debug_test_target)
                if mode.shared_lib:
                    build_dependencies.append(test_gcc_debug_test_target_shared)
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_gcc_debug)
                if mode.shared_lib:
                    build_dependencies.append(install_gcc_debug_shared)

        if mode.release:
            if mode.static_lib:
                build_dependencies.append(build_gcc_relwithdebinfo_all)
            if mode.shared_lib:
                build_dependencies.append(build_gcc_relwithdebinfo_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_relwithdebinfo)
                if mode.shared_lib:
                    build_dependencies.append(test_gcc_relwithdebinfo_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_relwithdebinfo_test_target)
                if mode.shared_lib:
                    build_dependencies.append(
                        test_gcc_relwithdebinfo_test_target_shared
                    )
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_gcc_relwithdebinfo)
                if mode.shared_lib:
                    build_dependencies.append(install_gcc_relwithdebinfo_shared)

            if mode.static_lib:
                build_dependencies.append(build_gcc_release_all)
            if mode.shared_lib:
                build_dependencies.append(build_gcc_release_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_release)
                if mode.shared_lib:
                    build_dependencies.append(test_gcc_release_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_gcc_release_test_target)
                if mode.shared_lib:
                    build_dependencies.append(test_gcc_release_test_target_shared)
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_gcc_release)
                if mode.shared_lib:
                    build_dependencies.append(install_gcc_release_shared)

    if mode.clang:
        if mode.debug:
            if mode.static_lib:
                build_dependencies.append(build_clang_debug_all)
            if mode.shared_lib:
                build_dependencies.append(build_clang_debug_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_clang_debug)
                if mode.shared_lib:
                    build_dependencies.append(test_clang_debug_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_clang_debug_test_target)
                if mode.shared_lib:
                    build_dependencies.append(test_clang_debug_test_target_shared)
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_clang_debug)
                if mode.shared_lib:
                    build_dependencies.append(install_clang_debug_shared)

        if mode.release:
            if mode.static_lib:
                build_dependencies.append(build_clang_relwithdebinfo_all)
            if mode.shared_lib:
                build_dependencies.append(build_clang_relwithdebinfo_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_clang_relwithdebinfo)
                if mode.shared_lib:
                    build_dependencies.append(test_clang_relwithdebinfo_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_clang_relwithdebinfo_test_target)
                if mode.shared_lib:
                    build_dependencies.append(
                        test_clang_relwithdebinfo_test_target_shared
                    )
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_clang_relwithdebinfo)
                if mode.shared_lib:
                    build_dependencies.append(install_clang_relwithdebinfo_shared)

            if mode.static_lib:
                build_dependencies.append(build_clang_release_all)
            if mode.shared_lib:
                build_dependencies.append(build_clang_release_all_shared)
            if mode.test:
                if mode.static_lib:
                    build_dependencies.append(test_clang_release)
                if mode.shared_lib:
                    build_dependencies.append(test_clang_release_shared)
            if mode.test_target:
                if mode.static_lib:
                    build_dependencies.append(test_clang_release_test_target)
                if mode.shared_lib:
                    build_dependencies.append(test_clang_release_test_target_shared)
            if mode.install:
                if mode.static_lib:
                    build_dependencies.append(install_clang_release)
                if mode.shared_lib:
                    build_dependencies.append(install_clang_release_shared)

    if mode.install:
        if mode.static_lib:
            build_dependencies.append(verify_install_contents_static)
        if mode.shared_lib:
            build_dependencies.append(verify_install_contents_shared)

    if mode.coverage:
        if mode.gcc:
            build_dependencies.append(analyze_gcc_coverage)

    if mode.valgrind:
        if mode.gcc:
            build_dependencies.append(test_gcc_valgrind)
        if mode.clang:
            build_dependencies.append(test_clang_valgrind)

    if mode.test_install:
        if mode.gcc:
            if mode.static_lib:
                if mode.debug:
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_debug_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_debug_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_debug_test
                    )
                if mode.release:
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_release_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_release_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_release_test
                    )

            if mode.shared_lib:
                if mode.debug:
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_debug_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_debug_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_debug_test_shared
                    )
                if mode.release:
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_no_version_gcc_release_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_gcc_release_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_gcc_release_test_shared
                    )

        if mode.clang:
            if mode.static_lib:
                if mode.debug:
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_debug_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_debug_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_debug_test
                    )
                if mode.release:
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_release_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_release_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_relwithdebinfo_test
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_release_test
                    )

            if mode.shared_lib:
                if mode.debug:
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_debug_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_debug_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_debug_test_shared
                    )
                if mode.release:
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_no_version_clang_release_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_find_package_exact_version_clang_release_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_relwithdebinfo_test_shared
                    )
                    build_dependencies.append(
                        test_install_add_subdirectory_clang_release_test_shared
                    )

    if mode.examples:
        build_dependencies.append(example_quick_start_build_and_install)
        build_dependencies.append(example_quick_start_add_subdirectory)

    if mode.static_analysis:
        if mode.clang:
            if mode.incremental:
                build_dependencies.append(run_clang_static_analysis_changed_files)
            else:
                build_dependencies.append(run_clang_static_analysis_all_files)

    prebuild = Task("Pre-build")
    prebuild.depends_on(prebuild_dependencies)
    build = Task("Build")
    build.depends_on(build_dependencies)

    success = prebuild.run()
    if not success:
        return 1

    success = build.run()
    if not success:
        return 1

    print(f"Success: {os.path.basename(sys.argv[0])}")

    return 0


if __name__ == "__main__":
    exit(main())
