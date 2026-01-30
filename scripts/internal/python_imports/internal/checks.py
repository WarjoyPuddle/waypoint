# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib
import re

from .cmake import install_dir_from_preset
from .file_types import is_cpp_header_file
from .files import find_all_files
from .files import find_files_by_name


def check_no_spaces_in_paths_(root_dir: pathlib.Path) -> bool:
    files = find_all_files(root_dir)

    for f in files:
        assert root_dir in f.parents
    files_strings = [str(f)[len(str(root_dir)) + 1 :] for f in files]

    for f in files_strings:
        if " " in f:
            print(f"Error ({f}):\nNo spaces allowed in file paths")

            return False

    return True


def check_main_header_has_no_includes_(main_header_path) -> bool:
    with open(main_header_path, "r") as f:
        contents = f.read()

    return re.search(r"# *include", contents) is None


def check_headers_contain_pragma_once_(root_dir) -> bool:
    files = find_files_by_name(root_dir, is_cpp_header_file)
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


def check_files_contain_only_allowed_characters(root_dir) -> bool:
    allowed_chars = set(
        "\n "
        "!\"#$%&'()*+,-./"
        "0123456789"
        ":;<=>?@"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "[\\]^_`"
        "abcdefghijklmnopqrstuvwxyz"
        "{|}~"
        "ÓóĄąĆćĘęŁłŃńŚśŹźŻż"
    )

    files = find_all_files(root_dir)
    for f in files:
        with open(f, "r") as file:
            text = file.read()

        for c in text:
            if c not in allowed_chars:
                print(f"Error ({f}):\nFile contains disallowed character {c}")

                return False

    return True


def misc_checks(root_dir, main_header_path) -> bool:
    success = check_main_header_has_no_includes_(main_header_path)
    if not success:
        print(f"Error: Header {main_header_path} must not include other headers")

        return False

    success = check_no_spaces_in_paths_(root_dir)
    if not success:
        print("Error: file paths must not contain spaces")

        return False

    success = check_headers_contain_pragma_once_(root_dir)
    if not success:
        print('Error: not all headers contain a "#pragma once" include guard')

        return False

    success = check_files_contain_only_allowed_characters(root_dir)
    if not success:
        print("Error: disallowed characters detected")

        return False

    return True


def verify_installation_contents_(
    preset, cmake_source_dir: pathlib.Path, expected_files: list[str]
) -> bool:
    install_dir = install_dir_from_preset(preset, cmake_source_dir)

    expected_paths = [(install_dir / f).resolve() for f in expected_files]
    expected_paths.sort()

    files = find_all_files(install_dir)
    files.sort()

    missing_files: list[pathlib.Path] = []
    for expected in expected_paths:
        if expected not in files:
            missing_files.append(expected)
    if len(missing_files) > 0:
        print("Some expected files are not in the installation directory:")
        for f in missing_files:
            print("  -", f)

        return False

    if len(files) != len(expected_paths):
        print("Unexpected files are present in the installation directory:")
        for f in files:
            if f not in expected_paths:
                print("  -", f)

        return False

    return True


def verify_installation_contents_static(preset, cmake_source_dir: pathlib.Path) -> bool:
    expected_files: list[str] = [
        "cmake/waypoint-config.cmake",
        "cmake/waypoint-config-debug.cmake",
        "cmake/waypoint-config-relwithdebinfo.cmake",
        "cmake/waypoint-config-release.cmake",
        "cmake/waypoint-config-version.cmake",
        "include/waypoint/waypoint.hpp",
        "lib/Debug/libassert.a",
        "lib/Debug/libcoverage.a",
        "lib/Debug/libprocess.a",
        "lib/Debug/libwaypoint.a",
        "lib/RelWithDebInfo/libassert.a",
        "lib/RelWithDebInfo/libcoverage.a",
        "lib/RelWithDebInfo/libprocess.a",
        "lib/RelWithDebInfo/libwaypoint.a",
        "lib/Release/libassert.a",
        "lib/Release/libcoverage.a",
        "lib/Release/libprocess.a",
        "lib/Release/libwaypoint.a",
    ]

    return verify_installation_contents_(preset, cmake_source_dir, expected_files)


def verify_installation_contents_shared(preset, cmake_source_dir: pathlib.Path) -> bool:
    expected_files: list[str] = [
        "cmake/waypoint-config.cmake",
        "cmake/waypoint-config-debug.cmake",
        "cmake/waypoint-config-relwithdebinfo.cmake",
        "cmake/waypoint-config-release.cmake",
        "cmake/waypoint-config-version.cmake",
        "include/waypoint/waypoint.hpp",
        "lib/Debug/libwaypoint.so",
        "lib/RelWithDebInfo/libwaypoint.so",
        "lib/Release/libwaypoint.so",
    ]

    return verify_installation_contents_(preset, cmake_source_dir, expected_files)
