# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import argparse
import dataclasses
import enum
import os
import pathlib

from python_imports import Task
from python_imports import analyze_gcc_coverage
from python_imports import build_cmake
from python_imports import cache_var_from_preset
from python_imports import changed_cpp_source_files_and_dependents
from python_imports import check_formatting
from python_imports import clang
from python_imports import clean_build_dir
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
from python_imports import run_clang_static_analysis
from python_imports import run_ctest
from python_imports import run_target
from python_imports import verify_installation_contents_shared
from python_imports import verify_installation_contents_static

THIS_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT_DIR = THIS_SCRIPT_DIR.resolve().parent.parent
BUILD_DIR = PROJECT_ROOT_DIR / "build___"


@enum.unique
class CMakePresets(enum.Enum):
    LinuxClang = (
        "configure_linux_clang",
        "build_linux_clang",
        "test_linux_clang",
    )
    LinuxGcc = (
        "configure_linux_gcc",
        "build_linux_gcc",
        "test_linux_gcc",
    )
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
    DefaultStatic = (
        "configure_static",
        "build_static",
        "test_static",
    )
    DefaultShared = (
        "configure_shared",
        "build_shared",
        "test_shared",
    )
    Example = (
        "configure",
        "build",
        "test",
    )
    AddressSanitizerClang = (
        "configure_linux_clang_address_sanitizer",
        "build_linux_clang_address_sanitizer",
        "test_linux_clang_address_sanitizer",
    )
    UndefinedBehaviourSanitizerClang = (
        "configure_linux_clang_undefined_behaviour_sanitizer",
        "build_linux_clang_undefined_behaviour_sanitizer",
        "test_linux_clang_undefined_behaviour_sanitizer",
    )
    LinuxClangValgrind = (
        "configure_linux_valgrind_clang",
        "build_linux_valgrind_clang",
        "test_linux_valgrind_clang",
    )
    LinuxGccValgrind = (
        "configure_linux_valgrind_gcc",
        "build_linux_valgrind_gcc",
        "test_linux_valgrind_gcc",
    )

    def __init__(
        self,
        configure_preset: str,
        build_preset: str,
        test_preset: str,
    ):
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


COVERAGE_DIR_GCOVR = BUILD_DIR / "coverage_gcovr_kMkR9SM1S69oCLJ5___"
COVERAGE_FILE_HTML_GCOVR = COVERAGE_DIR_GCOVR / "index.html"
COVERAGE_FILE_JSON_GCOVR = COVERAGE_DIR_GCOVR / "coverage.json"
INFRASTRUCTURE_DIR = PROJECT_ROOT_DIR / "infrastructure"
CMAKE_SOURCE_DIR = INFRASTRUCTURE_DIR
CMAKE_LISTS_FILE = CMAKE_SOURCE_DIR / "CMakeLists.txt"
CMAKE_PRESETS_FILE = CMAKE_SOURCE_DIR / "CMakePresets.json"
assert CMAKE_LISTS_FILE.is_file() and CMAKE_PRESETS_FILE.is_file()

CLANG_TIDY_CONFIG = INFRASTRUCTURE_DIR / ".clang-tidy-20"
assert CLANG_TIDY_CONFIG.is_file()
CLANG_FORMAT_CONFIG = INFRASTRUCTURE_DIR / ".clang-format-20"
assert CLANG_FORMAT_CONFIG.is_file()

MAIN_HEADER_PATH = PROJECT_ROOT_DIR / "src/waypoint/include/waypoint/waypoint.hpp"
assert MAIN_HEADER_PATH.is_file(), "waypoint.hpp does not exist"

INSTALL_TESTS_DIR_PATH = PROJECT_ROOT_DIR / "test/install_tests"
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR = (
    INSTALL_TESTS_DIR_PATH / "find_package_no_version_test"
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR = (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR / "infrastructure"
)
assert (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR = (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR = (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR = (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR = (
    TEST_INSTALL_FIND_PACKAGE_NO_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CMAKE_SOURCE_DIR,
    )
)

TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR = (
    INSTALL_TESTS_DIR_PATH / "find_package_exact_version_test"
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR = (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR / "infrastructure"
)
assert (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR = (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxClang,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR = (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxGcc,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR = (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR = (
    TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_INSTALL_DIR",
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CMAKE_SOURCE_DIR,
    )
)

TEST_INSTALL_ADD_SUBDIRECTORY_DIR = INSTALL_TESTS_DIR_PATH / "add_subdirectory_test"
TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR / "infrastructure"
)
assert (
    TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()

TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_SOURCES_PATH",
        "base_sources_path",
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )
)

TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_BUILD_PATH",
        CMakePresets.LinuxClang,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_BUILD_PATH",
        CMakePresets.LinuxGcc,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_SHARED_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_BUILD_PATH",
        CMakePresets.LinuxClangShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )
)
TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_SHARED_DIR = (
    TEST_INSTALL_ADD_SUBDIRECTORY_DIR
    / cache_var_from_preset(
        "PRESET_WAYPOINT_BUILD_PATH",
        CMakePresets.LinuxGccShared,
        TEST_INSTALL_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
    )
)

EXAMPLES_DIR_PATH = PROJECT_ROOT_DIR / "examples"
EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR = (
    EXAMPLES_DIR_PATH / "quick_start_build_and_install"
)
assert (
    EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()
EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR = (
    EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR / "waypoint_install___"
)

EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR = (
    EXAMPLES_DIR_PATH / "quick_start_add_subdirectory"
)
assert (
    EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()
EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR = (
    EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR / "third_party___"
)
EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR = (
    EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR / "waypoint"
)

EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR = (
    EXAMPLES_DIR_PATH / "quick_start_custom_main"
)
assert (
    EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR / "CMakeLists.txt"
).is_file() and (
    EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR / "CMakePresets.json"
).is_file()
EXAMPLE_QUICK_START_CUSTOM_MAIN_WAYPOINT_INSTALL_DIR = (
    EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR / "waypoint_install___"
)


@dataclasses.dataclass(frozen=True)
class ModeConfig:
    basic_static_build: bool = False
    basic_shared_build: bool = False
    clean: bool = False
    check_formatting: bool = False
    fix_formatting: bool = False
    static_lib: bool = False
    shared_lib: bool = False
    clang: bool = False
    gcc: bool = False
    debug: bool = False
    release: bool = False
    static_analysis_full: bool = False
    static_analysis_incremental: bool = False
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
    BasicStaticBuild = ModeConfig(basic_static_build=True)
    BasicSharedBuild = ModeConfig(basic_shared_build=True)
    Fast = ModeConfig(
        static_lib=True,
        clang=True,
        debug=True,
        test=True,
    )
    Format = ModeConfig(
        fix_formatting=True,
    )
    Clean = ModeConfig(
        clean=True,
    )
    Verify = ModeConfig(
        clean=True,
        check_formatting=True,
        static_lib=True,
        shared_lib=True,
        clang=True,
        gcc=True,
        debug=True,
        release=True,
        static_analysis_full=True,
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
    StaticAnalysisFull = ModeConfig(
        clang=True,
        static_analysis_full=True,
    )
    StaticAnalysisIncremental = ModeConfig(
        clang=True,
        static_analysis_incremental=True,
    )
    Valgrind = ModeConfig(
        clang=True,
        gcc=True,
        valgrind=True,
    )

    def __init__(self, config):
        self.config = config

    def __str__(self):
        if self == Mode.BasicStaticBuild:
            return "basic_static_build"
        if self == Mode.BasicSharedBuild:
            return "basic_shared_build"
        if self == Mode.Clean:
            return "clean"
        if self == Mode.Coverage:
            return "coverage"
        if self == Mode.Fast:
            return "fast"
        if self == Mode.Format:
            return "format"
        if self == Mode.StaticAnalysisFull:
            return "static_full"
        if self == Mode.StaticAnalysisIncremental:
            return "static_incremental"
        if self == Mode.Valgrind:
            return "valgrind"
        if self == Mode.Verify:
            return "verify"

        assert False, "This should not happen"

    @property
    def basic_static_build(self):
        return self.config.basic_static_build

    @property
    def basic_shared_build(self):
        return self.config.basic_shared_build

    @property
    def clean(self):
        return self.config.clean

    @property
    def incremental(self):
        return not self.config.clean

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
    def static_analysis_full(self):
        return self.config.static_analysis_full

    @property
    def static_analysis_incremental(self):
        return self.config.static_analysis_incremental

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


def install_default_clang_debug_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultStatic, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_default_clang_relwithdebinfo_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultStatic, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_default_clang_release_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultStatic, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
    )


def install_default_clang_debug_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultShared, CMakeBuildConfig.Debug, CMAKE_SOURCE_DIR
    )


def install_default_clang_relwithdebinfo_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultShared, CMakeBuildConfig.RelWithDebInfo, CMAKE_SOURCE_DIR
    )


def install_default_clang_release_shared_fn() -> bool:
    return install_cmake(
        CMakePresets.DefaultShared, CMakeBuildConfig.Release, CMAKE_SOURCE_DIR
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


def configure_default_clang_fn() -> bool:
    env_patch = {"CC": os.getenv("CC"), "CXX": os.getenv("CXX")}

    if None in env_patch.values():
        with clang():
            return configure_cmake(CMakePresets.DefaultStatic, CMAKE_SOURCE_DIR)

    return configure_cmake(CMakePresets.DefaultStatic, CMAKE_SOURCE_DIR)


def configure_default_clang_shared_fn() -> bool:
    env_patch = {"CC": os.getenv("CC"), "CXX": os.getenv("CXX")}

    if None in env_patch.values():
        with clang():
            return configure_cmake(CMakePresets.DefaultShared, CMAKE_SOURCE_DIR)

    return configure_cmake(CMakePresets.DefaultShared, CMAKE_SOURCE_DIR)


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

    files_from_db = get_files_from_compilation_database(
        CMakePresets.Example, EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR
    )
    inputs += [
        (
            f,
            CMakePresets.Example,
            EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
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


def configure_cmake_gcc_valgrind_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxGccValgrind, CMAKE_SOURCE_DIR)


def build_gcc_valgrind_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccValgrind,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_gcc_valgrind_debug_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxGccValgrind,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def configure_cmake_clang_valgrind_fn() -> bool:
    return configure_cmake(CMakePresets.LinuxClangValgrind, CMAKE_SOURCE_DIR)


def build_clang_debug_valgrind_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangValgrind,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_clang_debug_valgrind_all_tests_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.LinuxClangValgrind,
        CMAKE_SOURCE_DIR,
        "all_tests",
    )


def test_gcc_debug_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxGccValgrind,
        CMakeBuildConfig.Debug,
        r"^valgrind$",
        CMAKE_SOURCE_DIR,
    )


def test_clang_debug_valgrind_fn() -> bool:
    return run_ctest(
        CMakePresets.LinuxClangValgrind,
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
    return analyze_gcc_coverage(COVERAGE_FILE_JSON_GCOVR, COVERAGE_FILE_HTML_GCOVR)


def build_default_clang_debug_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.DefaultStatic,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_default_clang_relwithdebinfo_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.DefaultStatic,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_default_clang_release_all_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.DefaultStatic,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_default_clang_debug_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Debug,
        CMakePresets.DefaultShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_default_clang_relwithdebinfo_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.RelWithDebInfo,
        CMakePresets.DefaultShared,
        CMAKE_SOURCE_DIR,
        "all",
    )


def build_default_clang_release_all_shared_fn() -> bool:
    return build_cmake(
        CMakeBuildConfig.Release,
        CMakePresets.DefaultShared,
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


def check_formatting_fn() -> bool:
    files = find_all_files(PROJECT_ROOT_DIR)

    return check_formatting(files, CLANG_FORMAT_CONFIG)


def format_sources_fn() -> bool:
    files = find_all_files(PROJECT_ROOT_DIR)

    return format_files(files, CLANG_FORMAT_CONFIG)


class CliConfig:
    def __init__(self, mode_str):
        self.mode = None

        if mode_str == str(Mode.BasicStaticBuild):
            self.mode = Mode.BasicStaticBuild
        if mode_str == str(Mode.BasicSharedBuild):
            self.mode = Mode.BasicSharedBuild
        if mode_str == str(Mode.Clean):
            self.mode = Mode.Clean
        if mode_str == str(Mode.Coverage):
            self.mode = Mode.Coverage
        if mode_str == str(Mode.Fast):
            self.mode = Mode.Fast
        if mode_str == str(Mode.Format):
            self.mode = Mode.Format
        if mode_str == str(Mode.StaticAnalysisFull):
            self.mode = Mode.StaticAnalysisFull
        if mode_str == str(Mode.StaticAnalysisIncremental):
            self.mode = Mode.StaticAnalysisIncremental
        if mode_str == str(Mode.Valgrind):
            self.mode = Mode.Valgrind
        if mode_str == str(Mode.Verify):
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
            str(Mode.BasicStaticBuild),
            str(Mode.BasicSharedBuild),
            str(Mode.Clean),
            str(Mode.Coverage),
            str(Mode.Fast),
            str(Mode.Format),
            str(Mode.StaticAnalysisFull),
            str(Mode.StaticAnalysisIncremental),
            str(Mode.Valgrind),
            str(Mode.Verify),
        ],
        metavar="mode",
        help=f"""Selects build mode:
                 "{Mode.BasicStaticBuild}" builds Waypoint as a static library,
                 using CC and CXX environment variables for compiler selection;
                 "{Mode.BasicSharedBuild}" builds Waypoint as a shared library,
                 using CC and CXX environment variables for compiler selection;
                 "{Mode.Clean}" deletes the build trees;
                 "{Mode.Coverage}" measures test coverage;
                 "{Mode.Format}" formats source files;
                 "{Mode.Fast}" runs one build and tests for quick iterations;
                 "{Mode.StaticAnalysisFull}" performs static analysis on all files;
                 "{Mode.StaticAnalysisIncremental}" (in a Git repository; requires Git)
                 performs static analysis on all files with uncommited changes;
                 "{Mode.Valgrind}" runs Valgrind checks (memcheck, helgrind);
                 "{Mode.Verify}" runs "{Mode.Clean}" followed by all builds and checks.""",
    )

    parsed = parser.parse_args()

    config = CliConfig(parsed.mode)

    return config, True


def clean_fn() -> bool:
    remove_dir(BUILD_DIR)

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
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_CLANG_SHARED_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_NO_VERSION_GCC_SHARED_DIR)

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
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_CLANG_SHARED_DIR)
    remove_dir(TEST_INSTALL_FIND_PACKAGE_EXACT_VERSION_GCC_SHARED_DIR)

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
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_CLANG_BUILD_SHARED_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_DIR)
    remove_dir(TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_GCC_BUILD_SHARED_DIR)

    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR)

    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR)

    clean_build_dir(
        CMakePresets.Example, EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR
    )
    remove_dir(EXAMPLE_QUICK_START_CUSTOM_MAIN_WAYPOINT_INSTALL_DIR)

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
        TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR / "infrastructure",
    )
    recursively_copy_dir(
        PROJECT_ROOT_DIR / "src",
        TEST_INSTALL_ADD_SUBDIRECTORY_WAYPOINT_SOURCES_DIR / "src",
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

    # use as a static library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.DefaultStatic,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR,
    )

    with clang():
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

    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Debug,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.RelWithDebInfo,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Release,
        "test_program",
    )
    if not success:
        return False

    # use as a dynamic library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.DefaultShared,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_WAYPOINT_INSTALL_DIR,
    )

    with clang():
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

    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Debug,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.RelWithDebInfo,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_BUILD_AND_INSTALL_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Release,
        "test_program",
    )
    if not success:
        return False

    return True


def example_quick_start_custom_main_fn() -> bool:
    example_cmake_source_dir = EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR

    # use as a static library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.DefaultStatic,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_WAYPOINT_INSTALL_DIR,
    )

    with clang():
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

    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Debug,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.RelWithDebInfo,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Release,
        "test_program",
    )
    if not success:
        return False

    # use as a dynamic library
    clean_build_dir(CMakePresets.Example, example_cmake_source_dir)

    copy_install_dir(
        CMakePresets.DefaultShared,
        CMAKE_SOURCE_DIR,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_WAYPOINT_INSTALL_DIR,
    )

    with clang():
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

    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Debug,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.RelWithDebInfo,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_CUSTOM_MAIN_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Release,
        "test_program",
    )
    if not success:
        return False

    return True


def example_quick_start_add_subdirectory_fn() -> bool:
    remove_dir(EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_THIRD_PARTY_DIR)
    recursively_copy_dir(
        PROJECT_ROOT_DIR / "infrastructure",
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR / "infrastructure",
    )
    recursively_copy_dir(
        PROJECT_ROOT_DIR / "src",
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_WAYPOINT_SOURCE_DIR / "src",
    )

    example_cmake_source_dir = EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR

    with clang():
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

    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Debug,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.RelWithDebInfo,
        "test_program",
    )
    if not success:
        return False
    success, output = run_target(
        CMakePresets.Example,
        EXAMPLE_QUICK_START_ADD_SUBDIRECTORY_CMAKE_SOURCE_DIR,
        CMakeBuildConfig.Release,
        "test_program",
    )
    if not success:
        return False

    return True


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

    configure_cmake_gcc_valgrind = Task(
        "Configure CMake for GCC with Valgrind", configure_cmake_gcc_valgrind_fn
    )
    build_gcc_valgrind_debug_all = Task(
        "Build GCC Debug for Valgrind (all)", build_gcc_valgrind_debug_all_fn
    )
    build_gcc_valgrind_debug_all.depends_on([configure_cmake_gcc_valgrind])
    build_gcc_valgrind_debug_all_tests = Task(
        "Build GCC Debug for Valgrind (all_tests)",
        build_gcc_valgrind_debug_all_tests_fn,
    )
    build_gcc_valgrind_debug_all_tests.depends_on([build_gcc_valgrind_debug_all])
    test_gcc_debug_valgrind = Task(
        "Test GCC Debug build with Valgrind", test_gcc_debug_valgrind_fn
    )
    test_gcc_debug_valgrind.depends_on([build_gcc_valgrind_debug_all_tests])

    configure_cmake_clang_valgrind = Task(
        "Configure CMake for Clang with Valgrind", configure_cmake_clang_valgrind_fn
    )
    build_clang_debug_valgrind_all = Task(
        "Build Clang for Valgrind (all)", build_clang_debug_valgrind_all_fn
    )
    build_clang_debug_valgrind_all.depends_on([configure_cmake_clang_valgrind])
    build_clang_debug_valgrind_all_tests = Task(
        "Build Clang for Valgrind (all_tests)", build_clang_debug_valgrind_all_tests_fn
    )
    build_clang_debug_valgrind_all_tests.depends_on([build_clang_debug_valgrind_all])
    test_clang_debug_valgrind = Task(
        "Test Clang build with Valgrind", test_clang_debug_valgrind_fn
    )
    test_clang_debug_valgrind.depends_on([build_clang_debug_valgrind_all_tests])

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

    configure_default_clang = Task(
        "Configure default Clang (static)", configure_default_clang_fn
    )
    build_default_clang_debug_all = Task(
        "Build default Clang Debug (static)", build_default_clang_debug_all_fn
    )
    build_default_clang_relwithdebinfo_all = Task(
        "Build default Clang RelWithDebInfo (static)",
        build_default_clang_relwithdebinfo_all_fn,
    )
    build_default_clang_release_all = Task(
        "Build default Clang Release (static)", build_default_clang_release_all_fn
    )
    install_default_clang_debug = Task(
        "Install default Clang Debug (static)", install_default_clang_debug_fn
    )
    install_default_clang_relwithdebinfo = Task(
        "Install default Clang RelWithDebInfo (static)",
        install_default_clang_relwithdebinfo_fn,
    )
    install_default_clang_release = Task(
        "Install default Clang Release (static)", install_default_clang_release_fn
    )
    configure_default_clang_shared = Task(
        "Configure default Clang (dynamic)", configure_default_clang_shared_fn
    )
    build_default_clang_debug_all_shared = Task(
        "Build default Clang Debug (dynamic)", build_default_clang_debug_all_shared_fn
    )
    build_default_clang_relwithdebinfo_all_shared = Task(
        "Build default Clang RelWithDebInfo (dynamic)",
        build_default_clang_relwithdebinfo_all_shared_fn,
    )
    build_default_clang_release_all_shared = Task(
        "Build default Clang Release (dynamic)",
        build_default_clang_release_all_shared_fn,
    )
    install_default_clang_debug_shared = Task(
        "Install default Clang Debug (dynamic)", install_default_clang_debug_shared_fn
    )
    install_default_clang_relwithdebinfo_shared = Task(
        "Install default Clang RelWithDebInfo (dynamic)",
        install_default_clang_relwithdebinfo_shared_fn,
    )
    install_default_clang_release_shared = Task(
        "Install default Clang Release (dynamic)",
        install_default_clang_release_shared_fn,
    )
    build_default_clang_debug_all.depends_on([configure_default_clang])
    build_default_clang_relwithdebinfo_all.depends_on([configure_default_clang])
    build_default_clang_release_all.depends_on([configure_default_clang])
    build_default_clang_debug_all_shared.depends_on([configure_default_clang_shared])
    build_default_clang_relwithdebinfo_all_shared.depends_on(
        [configure_default_clang_shared]
    )
    build_default_clang_release_all_shared.depends_on([configure_default_clang_shared])
    install_default_clang_debug.depends_on([build_default_clang_debug_all])
    install_default_clang_relwithdebinfo.depends_on(
        [build_default_clang_relwithdebinfo_all]
    )
    install_default_clang_release.depends_on([build_default_clang_release_all])
    install_default_clang_debug_shared.depends_on(
        [build_default_clang_debug_all_shared]
    )
    install_default_clang_relwithdebinfo_shared.depends_on(
        [build_default_clang_relwithdebinfo_all_shared]
    )
    install_default_clang_release_shared.depends_on(
        [build_default_clang_release_all_shared]
    )
    example_quick_start_build_and_install = Task(
        "Test examples/quick_start_build_and_install",
        example_quick_start_build_and_install_fn,
    )
    example_quick_start_build_and_install.depends_on(
        [
            install_default_clang_debug,
            install_default_clang_relwithdebinfo,
            install_default_clang_release,
            install_default_clang_debug_shared,
            install_default_clang_relwithdebinfo_shared,
            install_default_clang_release_shared,
        ]
    )

    example_quick_start_add_subdirectory = Task(
        "Test examples/quick_start_add_subdirectory",
        example_quick_start_add_subdirectory_fn,
    )

    example_quick_start_custom_main = Task(
        "Test examples/quick_start_custom_main",
        example_quick_start_custom_main_fn,
    )
    example_quick_start_custom_main.depends_on(
        [
            install_default_clang_debug,
            install_default_clang_relwithdebinfo,
            install_default_clang_release,
            install_default_clang_debug_shared,
            install_default_clang_relwithdebinfo_shared,
            install_default_clang_release_shared,
        ]
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
            example_quick_start_custom_main,
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
            example_quick_start_custom_main,
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

    if mode.check_formatting:
        build_dependencies.append(check_formatting_task)

    if mode.fix_formatting:
        build_dependencies.append(format_sources)

    if mode.misc:
        build_dependencies.append(misc_checks_task)

    if mode.address_sanitizer:
        build_dependencies.extend(
            [
                test_clang_address_sanitizer_debug,
                test_clang_address_sanitizer_relwithdebinfo,
                test_clang_address_sanitizer_release,
            ]
        )

    if mode.undefined_behaviour_sanitizer:
        build_dependencies.extend(
            [
                test_clang_undefined_behaviour_sanitizer_debug,
                test_clang_undefined_behaviour_sanitizer_relwithdebinfo,
                test_clang_undefined_behaviour_sanitizer_release,
            ]
        )

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
            build_dependencies.append(test_gcc_debug_valgrind)
        if mode.clang:
            build_dependencies.append(test_clang_debug_valgrind)

    if mode.test_install:
        if mode.gcc:
            if mode.static_lib:
                if mode.debug:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_gcc_debug_test,
                            test_install_find_package_exact_version_gcc_debug_test,
                            test_install_add_subdirectory_gcc_debug_test,
                        ]
                    )
                if mode.release:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_gcc_relwithdebinfo_test,
                            test_install_find_package_no_version_gcc_release_test,
                            test_install_find_package_exact_version_gcc_relwithdebinfo_test,
                            test_install_find_package_exact_version_gcc_release_test,
                            test_install_add_subdirectory_gcc_relwithdebinfo_test,
                            test_install_add_subdirectory_gcc_release_test,
                        ]
                    )

            if mode.shared_lib:
                if mode.debug:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_gcc_debug_test_shared,
                            test_install_find_package_exact_version_gcc_debug_test_shared,
                            test_install_add_subdirectory_gcc_debug_test_shared,
                        ]
                    )
                if mode.release:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_gcc_relwithdebinfo_test_shared,
                            test_install_find_package_no_version_gcc_release_test_shared,
                            test_install_find_package_exact_version_gcc_relwithdebinfo_test_shared,
                            test_install_find_package_exact_version_gcc_release_test_shared,
                            test_install_add_subdirectory_gcc_relwithdebinfo_test_shared,
                            test_install_add_subdirectory_gcc_release_test_shared,
                        ]
                    )

        if mode.clang:
            if mode.static_lib:
                if mode.debug:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_clang_debug_test,
                            test_install_find_package_exact_version_clang_debug_test,
                            test_install_add_subdirectory_clang_debug_test,
                        ]
                    )
                if mode.release:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_clang_relwithdebinfo_test,
                            test_install_find_package_no_version_clang_release_test,
                            test_install_find_package_exact_version_clang_relwithdebinfo_test,
                            test_install_find_package_exact_version_clang_release_test,
                            test_install_add_subdirectory_clang_relwithdebinfo_test,
                            test_install_add_subdirectory_clang_release_test,
                        ]
                    )

            if mode.shared_lib:
                if mode.debug:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_clang_debug_test_shared,
                            test_install_find_package_exact_version_clang_debug_test_shared,
                            test_install_add_subdirectory_clang_debug_test_shared,
                        ]
                    )
                if mode.release:
                    build_dependencies.extend(
                        [
                            test_install_find_package_no_version_clang_relwithdebinfo_test_shared,
                            test_install_find_package_no_version_clang_release_test_shared,
                            test_install_find_package_exact_version_clang_relwithdebinfo_test_shared,
                            test_install_find_package_exact_version_clang_release_test_shared,
                            test_install_add_subdirectory_clang_relwithdebinfo_test_shared,
                            test_install_add_subdirectory_clang_release_test_shared,
                        ]
                    )

    if mode.examples:
        build_dependencies.extend(
            [
                example_quick_start_build_and_install,
                example_quick_start_add_subdirectory,
                example_quick_start_custom_main,
            ]
        )

    if mode.static_analysis_full:
        build_dependencies.append(run_clang_static_analysis_all_files_task)

    if mode.static_analysis_incremental:
        build_dependencies.append(run_clang_static_analysis_changed_files_task)

    if mode.basic_static_build:
        build_dependencies.extend(
            [
                install_default_clang_debug,
                install_default_clang_relwithdebinfo,
                install_default_clang_release,
            ]
        )

    if mode.basic_shared_build:
        build_dependencies.extend(
            [
                install_default_clang_debug_shared,
                install_default_clang_relwithdebinfo_shared,
                install_default_clang_release_shared,
            ]
        )

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

    return 0


if __name__ == "__main__":
    exit(main())
