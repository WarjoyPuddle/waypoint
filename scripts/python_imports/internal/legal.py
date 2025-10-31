# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import datetime
import hashlib
import multiprocessing
import os
import re
import sys
import typing

from .file_types import is_bash_file
from .file_types import is_cmake_file
from .file_types import is_cpp_file
from .file_types import is_docker_file
from .file_types import is_python_file
from .system import get_cpu_count

COPYRIGHT_HOLDER_NAME = "Wojciech Kałuża"
EXPECTED_SPDX_LICENSE_ID = "MIT"


def is_file_in_need_of_licensing_comment(f) -> bool:
    return (
        is_bash_file(f)
        or is_cmake_file(f)
        or is_cpp_file(f)
        or is_docker_file(f)
        or is_python_file(f)
    )


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


def check_copyright_comments(files) -> bool:
    inputs = [f for f in files if is_file_in_need_of_licensing_comment(f)]
    with multiprocessing.Pool(get_cpu_count()) as pool:
        results = pool.map(check_copyright_comments_in_single_file, inputs)
    errors = [(output, file) for success, output, file in results if not success]
    if len(errors) > 0:
        for output, file in errors:
            print(f"Error: {file}\nIncorrect copyright comment")
            if output is not None:
                print(output)

        return False

    return True


def check_license_file(license_file_path) -> bool:
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
