# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import argparse
import contextlib
import dataclasses
import enum
import os
import sys

from python_imports import Compiler
from python_imports import Task
from python_imports import analyze_gcc_coverage
from python_imports import build_cmake
from python_imports import build_dir_from_preset
from python_imports import changed_cpp_source_files_and_dependents
from python_imports import check_copyright_comments
from python_imports import check_formatting
from python_imports import check_license_file
from python_imports import clean_build_dir
from python_imports import clean_install_dir
from python_imports import configure_cmake
from python_imports import copy_install_dir
from python_imports import find_all_cpp_source_files
from python_imports import find_all_files
from python_imports import format_files
from python_imports import get_files_from_compilation_database
from python_imports import install_cmake
from python_imports import is_supported_os
from python_imports import misc_checks
from python_imports import process_coverage
from python_imports import recursively_copy_dir
from python_imports import remove_dir
from python_imports import run
from python_imports import run_clang_static_analysis
from python_imports import run_ctest
from python_imports import verify_installation_contents_shared
from python_imports import verify_installation_contents_static

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/..")

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

CLANG_TIDY_CONFIG = os.path.realpath(f"{INFRASTRUCTURE_DIR}/.clang-tidy-20")
CLANG_FORMAT_CONFIG = os.path.realpath(f"{INFRASTRUCTURE_DIR}/.clang-format-20")

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

LICENSE_FILE_PATH = os.path.realpath(f"{PROJECT_ROOT_DIR}/LICENSE")


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
    address_sanitizer: bool = False
    undefined_behaviour_sanitizer: bool = False
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
        address_sanitizer=True,
        undefined_behaviour_sanitizer=True,
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
        address_sanitizer=True,
        undefined_behaviour_sanitizer=True,
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
    def address_sanitizer(self):
        return self.config.address_sanitizer

    @property
    def undefined_behaviour_sanitizer(self):
        return self.config.undefined_behaviour_sanitizer

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
    LinuxClang = (
        Compiler.Clang,
        "configure_linux_clang",
        "build_linux_clang",
        "test_linux_clang",
    )
    LinuxGcc = (
        Compiler.Gcc,
        "configure_linux_gcc",
        "build_linux_gcc",
        "test_linux_gcc",
    )
    LinuxClangShared = (
        Compiler.Clang,
        "configure_linux_clang_shared",
        "build_linux_clang_shared",
        "test_linux_clang_shared",
    )
    LinuxGccShared = (
        Compiler.Gcc,
        "configure_linux_gcc_shared",
        "build_linux_gcc_shared",
        "test_linux_gcc_shared",
    )
    LinuxGccCoverage = (
        Compiler.Gcc,
        "configure_linux_gcc_coverage",
        "build_linux_gcc_coverage",
        "test_linux_gcc_coverage",
    )
    Example = (
        Compiler.Clang,
        "example_configure",
        "example_build",
        "example_test",
    )
    ExampleShared = (
        Compiler.Clang,
        "example_configure_shared",
        "example_build_shared",
        "example_test_shared",
    )
    AddressSanitizerClang = (
        Compiler.Clang,
        "configure_linux_clang_address_sanitizer",
        "build_linux_clang_address_sanitizer",
        "test_linux_clang_address_sanitizer",
    )
    UndefinedBehaviourSanitizerClang = (
        Compiler.Clang,
        "configure_linux_clang_undefined_behaviour_sanitizer",
        "build_linux_clang_undefined_behaviour_sanitizer",
        "test_linux_clang_undefined_behaviour_sanitizer",
    )

    def __init__(
        self,
        compiler: Compiler,
        configure_preset: str,
        build_preset: str,
        test_preset: str,
    ):
        self._compiler = compiler
        self._configure_preset = configure_preset
        self._build_preset = build_preset
        self._test_preset = test_preset

    @property
    def compiler(self):
        return self._compiler

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


def misc_checks_fn() -> bool:
    return misc_checks(PROJECT_ROOT_DIR, MAIN_HEADER_PATH)


def verify_install_contents_static_fn() -> bool:
    success = verify_installation_contents_static(
        CMakePresets.LinuxClang, CMAKE_SOURCE_DIR
    )
    if not success:
        print("Error: Invalid Clang installation contents (static)")

        return False

    success = verify_installation_contents_static(
        CMakePresets.LinuxGcc, CMAKE_SOURCE_DIR
    )
    if not success:
        print("Error: Invalid GCC installation contents (static)")

        return False

    return True


def verify_install_contents_shared_fn() -> bool:
    success = verify_installation_contents_shared(
        CMakePresets.LinuxClangShared, CMAKE_SOURCE_DIR
    )
    if not success:
        print("Error: Invalid Clang installation contents (dynamic)")

        return False

    success = verify_installation_contents_shared(
        CMakePresets.LinuxGccShared, CMAKE_SOURCE_DIR
    )
    if not success:
        print("Error: Invalid GCC installation contents (dynamic)")

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
    return configure_cmake(CMakePresets.LinuxClang, CMAKE_SOURCE_DIR)


def configure_cmake_gcc_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxGcc, CMAKE_SOURCE_DIR)


def configure_cmake_clang_shared_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxClangShared, CMAKE_SOURCE_DIR)


def configure_cmake_gcc_shared_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxGccShared, CMAKE_SOURCE_DIR)


def configure_example_clang_fn() -> bool:
    return configure_cmake(CMakePresets.Example, CMAKE_SOURCE_DIR)


def configure_example_clang_shared_fn() -> bool:
    return configure_cmake(CMakePresets.ExampleShared, CMAKE_SOURCE_DIR)


def collect_inputs_for_static_analysis(all_files_set):
    inputs = []

    files_from_db = get_files_from_compilation_database(
        CMakePresets.LinuxClang, CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.LinuxClang,
            CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    files_from_db = get_files_from_compilation_database(
        CMakePresets.LinuxClang, TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.LinuxClang,
            TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    files_from_db = get_files_from_compilation_database(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
    inputs += [
        (
            f,
            CMakePresets.LinuxClang,
            TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    files_from_db = get_files_from_compilation_database(
        CMakePresets.LinuxClang, TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.LinuxClang,
            TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    files_from_db = get_files_from_compilation_database(
        CMakePresets.Example, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.Example,
            EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    files_from_db = get_files_from_compilation_database(
        CMakePresets.Example, EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.Example,
            EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
            PROJECT_ROOT_DIR,
            CLANG_TIDY_CONFIG,
        )
        for f in files_from_db
        if f in all_files_set
    ]

    return inputs


def run_clang_static_analysis_all_files_fn() -> bool:
    all_files_set = set(find_all_cpp_source_files(PROJECT_ROOT_DIR))
    inputs = collect_inputs_for_static_analysis(all_files_set)

    return run_clang_static_analysis(inputs)


def run_clang_static_analysis_changed_files_fn() -> bool:
    all_files_set = set(
        changed_cpp_source_files_and_dependents(
            PROJECT_ROOT_DIR, CMAKE_SOURCE_DIR, CMakePresets.LinuxClang
        )
    )
    inputs = collect_inputs_for_static_analysis(all_files_set)

    return run_clang_static_analysis(inputs)


def test_gcc_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc, CMakeBuildConfig.Debug, r"^test$", CMAKE_SOURCE_DIR
    )


def test_gcc_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_release_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_release_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_debug_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_relwithdebinfo_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_release_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_debug_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_relwithdebinfo_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_release_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_gcc_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        r"^valgrind$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        r"^valgrind$",
        CMAKE_SOURCE_DIR,
    )


def process_coverage_fn() -> bool:
    return process_coverage(
        CMakePresets.LinuxGccCoverage,
        CMAKE_SOURCE_DIR,
        PROJECT_ROOT_DIR,
        COVERAGE_DIR_GCOVR,
        COVERAGE_FILE_HTML_GCOVR,
        COVERAGE_FILE_JSON_GCOVR,
    )


def configure_cmake_gcc_coverage_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxGccCoverage, CMAKE_SOURCE_DIR)


def build_gcc_coverage_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccCoverage,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_coverage_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccCoverage,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_gcc_coverage_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccCoverage,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def analyze_gcc_coverage_fn() -> bool:
    return analyze_gcc_coverage(COVERAGE_FILE_JSON_GCOVR)


def build_example_clang_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.ExampleShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.ExampleShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_example_clang_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.ExampleShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_relwithdebinfo_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_release_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_debug_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_relwithdebinfo_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_gcc_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_release_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def check_copyright_comments_fn() -> bool:
    files = find_all_files(PROJECT_ROOT_DIR)

    return check_copyright_comments(files)


def check_formatting_fn() -> bool:
    files = find_all_files(PROJECT_ROOT_DIR)

    return check_formatting(files, CLANG_FORMAT_CONFIG)


def format_sources_fn() -> bool:
    files = find_all_files(PROJECT_ROOT_DIR)

    return format_files(files, CLANG_FORMAT_CONFIG)


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
    success = is_supported_os()
    if not success:
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
    clean_install_dir(CMakePresets.LinuxClang, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.LinuxGcc, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.LinuxClangShared, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.LinuxGccShared, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.LinuxGccCoverage, CMAKE_SOURCE_DIR)
    remove_dir(COVERAGE_DIR_GCOVR)
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
    clean_install_dir(CMakePresets.Example, CMAKE_SOURCE_DIR)
    clean_build_dir(CMakePresets.ExampleShared, CMAKE_SOURCE_DIR)
    clean_install_dir(CMakePresets.ExampleShared, CMAKE_SOURCE_DIR)
    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR)

    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR)

    clean_build_dir(CMakePresets.AddressSanitizerClang, CMAKE_SOURCE_DIR)
    clean_build_dir(CMakePresets.UndefinedBehaviourSanitizerClang, CMAKE_SOURCE_DIR)

    return True


def test_install_find_package_no_version_gcc_copy_artifacts_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR,
    )

    return True


def test_install_find_package_no_version_clang_copy_artifacts_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR,
    )

    return True


def test_install_find_package_no_version_gcc_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_copy_artifacts_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR,
    )

    return True


def test_install_find_package_exact_version_clang_copy_artifacts_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR,
    )

    return True


def test_install_find_package_exact_version_gcc_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_copy_artifacts_shared_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR,
    )

    return True


def test_install_find_package_no_version_clang_copy_artifacts_shared_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR,
    )

    return True


def test_install_find_package_no_version_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_gcc_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_no_version_clang_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_no_version_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_no_version_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_copy_artifacts_shared_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR,
    )

    return True


def test_install_find_package_exact_version_clang_copy_artifacts_shared_fn() -> bool:
    copy_install_dir(
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR,
    )

    return True


def test_install_find_package_exact_version_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_gcc_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_debug_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_find_package_exact_version_clang_release_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_find_package_exact_version_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_relwithdebinfo_test_shared_fn() -> (
    bool
):
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )


def test_install_find_package_exact_version_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
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
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_configure_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_debug_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_debug_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_release_build_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_release_build_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGcc,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_debug_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_relwithdebinfo_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_release_test_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClang,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_configure_shared_fn() -> bool:
    return configure_cmake(
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_gcc_release_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_debug_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_debug_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_relwithdebinfo_build_all_tests_shared_fn() -> (
    bool
):
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_clang_release_build_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all",
    )


def test_install_add_subdirectory_clang_release_build_all_tests_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_install_add_subdirectory_gcc_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_gcc_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccShared,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_debug_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Debug,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_relwithdebinfo_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_install_add_subdirectory_clang_release_test_shared_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangShared,
        CMakeBuildConfig.Release,
        r"^test$",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )


def test_clang_debug_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_relwithdebinfo_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_release_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClang,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_debug_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_relwithdebinfo_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_clang_release_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxClangShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_debug_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_relwithdebinfo_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_release_test_target_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGcc,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_debug_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_relwithdebinfo_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def test_gcc_release_test_target_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.LinuxGccShared,
        CMAKE_SOURCE_DIR,
        "test",
    )


def example_quick_start_build_and_install_fn() -> bool:
    example_cmake_source_dir = EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR

    # use Waypoint as a static library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.Example,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR,
    )

    success = configure_cmake(CMakePresets.Example, example_cmake_source_dir)
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False

    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Debug,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.RelWithDebInfo,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Release,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False

    with contextlib.chdir(example_cmake_source_dir):
        build_dir = build_dir_from_preset(
            CMakePresets.Example, example_cmake_source_dir
        )

        success, output = run([f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"])
        if not success:
            return False
        success, output = run(
            [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
        )
        if not success:
            return False
        success, output = run([f"{build_dir}/{CMakeBuildConfig.Release}/test_program"])
        if not success:
            return False

    # use Waypoint as a dynamic library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.ExampleShared,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR,
    )

    success = configure_cmake(CMakePresets.Example, example_cmake_source_dir)
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False

    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Debug,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.RelWithDebInfo,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Release,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False

    with contextlib.chdir(example_cmake_source_dir):
        build_dir = build_dir_from_preset(
            CMakePresets.Example, example_cmake_source_dir
        )

        success, output = run([f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"])
        if not success:
            return False
        success, output = run(
            [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
        )
        if not success:
            return False
        success, output = run([f"{build_dir}/{CMakeBuildConfig.Release}/test_program"])
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

    success = configure_cmake(CMakePresets.Example, example_cmake_source_dir)
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "all",
    )
    if not success:
        return False

    success = build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False
    success = build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.Example,
        example_cmake_source_dir,
        "test",
    )
    if not success:
        return False

    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Debug,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.RelWithDebInfo,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False
    success = run_ctest(
        CMakePresets.Example,
        CMakeBuildConfig.Release,
        None,
        example_cmake_source_dir,
    )
    if not success:
        return False

    with contextlib.chdir(example_cmake_source_dir):
        build_dir = build_dir_from_preset(
            CMakePresets.Example, example_cmake_source_dir
        )

        success, output = run([f"{build_dir}/{CMakeBuildConfig.Debug}/test_program"])
        if not success:
            return False
        success, output = run(
            [f"{build_dir}/{CMakeBuildConfig.RelWithDebInfo}/test_program"]
        )
        if not success:
            return False
        success, output = run([f"{build_dir}/{CMakeBuildConfig.Release}/test_program"])
        if not success:
            return False

    return True


def check_license_file_fn() -> bool:
    return check_license_file(LICENSE_FILE_PATH)


def configure_clang_address_sanitizer_fn() -> bool:
    return configure_cmake(CMakePresets.AddressSanitizerClang, CMAKE_SOURCE_DIR)


def build_clang_address_sanitizer_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_address_sanitizer_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_address_sanitizer_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_address_sanitizer_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_address_sanitizer_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_address_sanitizer_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.AddressSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_clang_address_sanitizer_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.AddressSanitizerClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_address_sanitizer_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.AddressSanitizerClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_address_sanitizer_release_fn() -> bool:
    return run_ctest(
        CMakePresets.AddressSanitizerClang,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def configure_clang_undefined_behaviour_sanitizer_fn() -> bool:
    return configure_cmake(
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
    )


def build_clang_undefined_behaviour_sanitizer_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_undefined_behaviour_sanitizer_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_undefined_behaviour_sanitizer_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def build_clang_undefined_behaviour_sanitizer_release_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_clang_undefined_behaviour_sanitizer_debug_fn() -> bool:
    return run_ctest(
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMakeBuildConfig.Debug,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_undefined_behaviour_sanitizer_relwithdebinfo_fn() -> bool:
    return run_ctest(
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMakeBuildConfig.RelWithDebInfo,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_undefined_behaviour_sanitizer_release_fn() -> bool:
    return run_ctest(
        CMakePresets.UndefinedBehaviourSanitizerClang,
        CMakeBuildConfig.Release,
        r"^test$",
        CMAKE_SOURCE_DIR,
    )


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

    analyze_gcc_coverage_task = Task(
        "Analyze GCC coverage data", analyze_gcc_coverage_fn
    )
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

    analyze_gcc_coverage_task.depends_on([process_gcc_coverage])
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
    run_clang_static_analysis_all_files_task = Task(
        "Run clang-tidy", run_clang_static_analysis_all_files_fn
    )
    run_clang_static_analysis_changed_files_task = Task(
        "Run clang-tidy (incremental)", run_clang_static_analysis_changed_files_fn
    )

    misc_checks_task = Task("Miscellaneous checks", misc_checks_fn)
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

    check_license_file_task = Task("Check LICENSE file", check_license_file_fn)
    check_copyright_comments_task = Task(
        "Check copyright comments", check_copyright_comments_fn
    )
    check_formatting_task = Task("Check code formatting", check_formatting_fn)
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

    run_clang_static_analysis_all_files_task.depends_on(
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
    run_clang_static_analysis_changed_files_task.depends_on(
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

    configure_clang_address_sanitizer = Task(
        "Configure CMake Clang Address Sanitizer", configure_clang_address_sanitizer_fn
    )

    build_clang_address_sanitizer_debug_all = Task(
        "Build Clang Address Sanitizer Debug all",
        build_clang_address_sanitizer_debug_all_fn,
    )
    build_clang_address_sanitizer_relwithdebinfo_all = Task(
        "Build Clang Address Sanitizer RelWithDebInfo all",
        build_clang_address_sanitizer_relwithdebinfo_all_fn,
    )
    build_clang_address_sanitizer_release_all = Task(
        "Build Clang Address Sanitizer Release all",
        build_clang_address_sanitizer_release_all_fn,
    )

    build_clang_address_sanitizer_debug_all.depends_on(
        [configure_clang_address_sanitizer]
    )
    build_clang_address_sanitizer_relwithdebinfo_all.depends_on(
        [configure_clang_address_sanitizer]
    )
    build_clang_address_sanitizer_release_all.depends_on(
        [configure_clang_address_sanitizer]
    )

    build_clang_address_sanitizer_debug_all_tests = Task(
        "Build Clang Address Sanitizer Debug all_tests",
        build_clang_address_sanitizer_debug_all_tests_fn,
    )
    build_clang_address_sanitizer_relwithdebinfo_all_tests = Task(
        "Build Clang Address Sanitizer RelWithDebInfo all_tests",
        build_clang_address_sanitizer_relwithdebinfo_all_tests_fn,
    )
    build_clang_address_sanitizer_release_all_tests = Task(
        "Build Clang Address Sanitizer Release all_tests",
        build_clang_address_sanitizer_release_all_tests_fn,
    )

    build_clang_address_sanitizer_debug_all_tests.depends_on(
        [build_clang_address_sanitizer_debug_all]
    )
    build_clang_address_sanitizer_relwithdebinfo_all_tests.depends_on(
        [build_clang_address_sanitizer_relwithdebinfo_all]
    )
    build_clang_address_sanitizer_release_all_tests.depends_on(
        [build_clang_address_sanitizer_release_all]
    )

    test_clang_address_sanitizer_debug = Task(
        "Test Clang Address Sanitizer Debug", test_clang_address_sanitizer_debug_fn
    )
    test_clang_address_sanitizer_relwithdebinfo = Task(
        "Test Clang Address Sanitizer RelWithDebInfo",
        test_clang_address_sanitizer_relwithdebinfo_fn,
    )
    test_clang_address_sanitizer_release = Task(
        "Test Clang Address Sanitizer Release", test_clang_address_sanitizer_release_fn
    )

    test_clang_address_sanitizer_debug.depends_on(
        [build_clang_address_sanitizer_debug_all_tests]
    )
    test_clang_address_sanitizer_relwithdebinfo.depends_on(
        [build_clang_address_sanitizer_relwithdebinfo_all_tests]
    )
    test_clang_address_sanitizer_release.depends_on(
        [build_clang_address_sanitizer_release_all_tests]
    )

    configure_clang_undefined_behaviour_sanitizer = Task(
        "Configure CMake Clang Undefined Behaviour Sanitizer",
        configure_clang_undefined_behaviour_sanitizer_fn,
    )

    build_clang_undefined_behaviour_sanitizer_debug_all = Task(
        "Build Clang Undefined Behaviour Sanitizer Debug all",
        build_clang_undefined_behaviour_sanitizer_debug_all_fn,
    )
    build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all = Task(
        "Build Clang Undefined Behaviour Sanitizer RelWithDebInfo all",
        build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_fn,
    )
    build_clang_undefined_behaviour_sanitizer_release_all = Task(
        "Build Clang Undefined Behaviour Sanitizer Release all",
        build_clang_undefined_behaviour_sanitizer_release_all_fn,
    )

    build_clang_undefined_behaviour_sanitizer_debug_all.depends_on(
        [configure_clang_undefined_behaviour_sanitizer]
    )
    build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all.depends_on(
        [configure_clang_undefined_behaviour_sanitizer]
    )
    build_clang_undefined_behaviour_sanitizer_release_all.depends_on(
        [configure_clang_undefined_behaviour_sanitizer]
    )

    build_clang_undefined_behaviour_sanitizer_debug_all_tests = Task(
        "Build Clang Undefined Behaviour Sanitizer Debug all_tests",
        build_clang_undefined_behaviour_sanitizer_debug_all_tests_fn,
    )
    build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_tests = Task(
        "Build Clang Undefined Behaviour Sanitizer RelWithDebInfo all_tests",
        build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_tests_fn,
    )
    build_clang_undefined_behaviour_sanitizer_release_all_tests = Task(
        "Build Clang Undefined Behaviour Sanitizer Release all_tests",
        build_clang_undefined_behaviour_sanitizer_release_all_tests_fn,
    )

    build_clang_undefined_behaviour_sanitizer_debug_all_tests.depends_on(
        [build_clang_undefined_behaviour_sanitizer_debug_all]
    )
    build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_tests.depends_on(
        [build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all]
    )
    build_clang_undefined_behaviour_sanitizer_release_all_tests.depends_on(
        [build_clang_undefined_behaviour_sanitizer_release_all]
    )

    test_clang_undefined_behaviour_sanitizer_debug = Task(
        "Test Clang Undefined Behaviour Sanitizer Debug",
        test_clang_undefined_behaviour_sanitizer_debug_fn,
    )
    test_clang_undefined_behaviour_sanitizer_relwithdebinfo = Task(
        "Test Clang Undefined Behaviour Sanitizer RelWithDebInfo",
        test_clang_undefined_behaviour_sanitizer_relwithdebinfo_fn,
    )
    test_clang_undefined_behaviour_sanitizer_release = Task(
        "Test Clang Undefined Behaviour Sanitizer Release",
        test_clang_undefined_behaviour_sanitizer_release_fn,
    )

    test_clang_undefined_behaviour_sanitizer_debug.depends_on(
        [build_clang_undefined_behaviour_sanitizer_debug_all_tests]
    )
    test_clang_undefined_behaviour_sanitizer_relwithdebinfo.depends_on(
        [build_clang_undefined_behaviour_sanitizer_relwithdebinfo_all_tests]
    )
    test_clang_undefined_behaviour_sanitizer_release.depends_on(
        [build_clang_undefined_behaviour_sanitizer_release_all_tests]
    )

    prebuild_dependencies = []
    build_dependencies = []

    if mode.clean:
        prebuild_dependencies.append(clean)

    if mode.check_legal:
        build_dependencies.append(check_license_file_task)
        build_dependencies.append(check_copyright_comments_task)

    if mode.check_formatting:
        build_dependencies.append(check_formatting_task)

    if mode.fix_formatting:
        build_dependencies.append(format_sources)

    if mode.misc:
        build_dependencies.append(misc_checks_task)

    if mode.address_sanitizer:
        build_dependencies.append(test_clang_address_sanitizer_debug)
        build_dependencies.append(test_clang_address_sanitizer_relwithdebinfo)
        build_dependencies.append(test_clang_address_sanitizer_release)

    if mode.undefined_behaviour_sanitizer:
        build_dependencies.append(test_clang_undefined_behaviour_sanitizer_debug)
        build_dependencies.append(
            test_clang_undefined_behaviour_sanitizer_relwithdebinfo
        )
        build_dependencies.append(test_clang_undefined_behaviour_sanitizer_release)

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
            build_dependencies.append(analyze_gcc_coverage_task)

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
                build_dependencies.append(run_clang_static_analysis_changed_files_task)
            else:
                build_dependencies.append(run_clang_static_analysis_all_files_task)

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
