# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os
import re

from .cmake import install_dir_from_preset
from .files import find_files_by_name, is_cpp_header_file


def check_no_spaces_in_paths_(root_dir) -> bool:
    files = find_files_by_name(root_dir, lambda x: True)

    for f in files:
        assert f.startswith(root_dir)
    files = [f[len(root_dir) + 1 :] for f in files]

    for f in files:
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

    return True


def verify_installation_contents_static(preset, cmake_source_dir) -> bool:
    install_dir = install_dir_from_preset(preset, cmake_source_dir)

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


def verify_installation_contents_shared(preset, cmake_source_dir) -> bool:
    install_dir = install_dir_from_preset(preset, cmake_source_dir)

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
