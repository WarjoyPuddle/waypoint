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


def verify_installation_contents_static(preset, cmake_source_dir: pathlib.Path) -> bool:
    install_dir = install_dir_from_preset(preset, cmake_source_dir)

    expected_files: list[pathlib.Path] = [
        install_dir / "cmake/waypoint-config.cmake",
        install_dir / "cmake/waypoint-config-debug.cmake",
        install_dir / "cmake/waypoint-config-relwithdebinfo.cmake",
        install_dir / "cmake/waypoint-config-release.cmake",
        install_dir / "cmake/waypoint-config-version.cmake",
        install_dir / "include/waypoint/waypoint.hpp",
        install_dir / "lib/Debug/libassert.a",
        install_dir / "lib/Debug/libcoverage.a",
        install_dir / "lib/Debug/libprocess.a",
        install_dir / "lib/Debug/libwaypoint_no_main_impl.a",
        install_dir / "lib/Debug/libwaypoint_main_impl.a",
        install_dir / "lib/RelWithDebInfo/libassert.a",
        install_dir / "lib/RelWithDebInfo/libcoverage.a",
        install_dir / "lib/RelWithDebInfo/libprocess.a",
        install_dir / "lib/RelWithDebInfo/libwaypoint_no_main_impl.a",
        install_dir / "lib/RelWithDebInfo/libwaypoint_main_impl.a",
        install_dir / "lib/Release/libassert.a",
        install_dir / "lib/Release/libcoverage.a",
        install_dir / "lib/Release/libprocess.a",
        install_dir / "lib/Release/libwaypoint_no_main_impl.a",
        install_dir / "lib/Release/libwaypoint_main_impl.a",
    ]
    expected_files = [f.resolve() for f in expected_files]

    files = find_all_files(install_dir)
    for expected in expected_files:
        assert expected in files, f"File not found: {expected}"

    assert len(files) == len(expected_files), "Unexpected files are present"

    return True


def verify_installation_contents_shared(preset, cmake_source_dir: pathlib.Path) -> bool:
    install_dir = install_dir_from_preset(preset, cmake_source_dir)

    expected_files: list[pathlib.Path] = [
        install_dir / "cmake/waypoint-config.cmake",
        install_dir / "cmake/waypoint-config-debug.cmake",
        install_dir / "cmake/waypoint-config-relwithdebinfo.cmake",
        install_dir / "cmake/waypoint-config-release.cmake",
        install_dir / "cmake/waypoint-config-version.cmake",
        install_dir / "include/waypoint/waypoint.hpp",
        install_dir / "lib/Debug/libwaypoint_no_main_impl.so",
        install_dir / "lib/Debug/libwaypoint_main_impl.so",
        install_dir / "lib/RelWithDebInfo/libwaypoint_no_main_impl.so",
        install_dir / "lib/RelWithDebInfo/libwaypoint_main_impl.so",
        install_dir / "lib/Release/libwaypoint_no_main_impl.so",
        install_dir / "lib/Release/libwaypoint_main_impl.so",
    ]
    expected_files = [f.resolve() for f in expected_files]

    files = find_all_files(install_dir)
    for expected in expected_files:
        assert expected in files, f"File not found: {expected}"

    assert len(files) == len(expected_files), "Unexpected files are present"

    return True
