# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import datetime
import hashlib
import json
import multiprocessing
import os
import re
import subprocess
import sys
import tempfile
import typing

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/..")
INFRASTRUCTURE_DIR = os.path.realpath(f"{PROJECT_ROOT_DIR}/infrastructure")

COPYRIGHT_HOLDER_NAME = "Wojciech Kałuża"
EXPECTED_SPDX_LICENSE_ID = "MIT"

PYTHON = (
    "python3" if (sys.executable is None or sys.executable == "") else sys.executable
)

JOBS = os.cpu_count()


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


def get_changed_files() -> typing.List[str]:
    assert os.getcwd() == PROJECT_ROOT_DIR
    success, output = run(["git", "diff", "--cached", "--name-only"])
    if not success:
        return find_files_by_name(PROJECT_ROOT_DIR, lambda x: True)

    files = output.strip().split("\n")
    out = []
    for f in files:
        path = os.path.realpath(f"{PROJECT_ROOT_DIR}/{f.strip()}")
        if os.path.isfile(path):
            out.append(path)

    out.sort()

    return out


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


def is_bash_file(f) -> bool:
    return re.search(r"\.bash$", f) is not None


def is_cmake_file(f) -> bool:
    return (
        re.search(r"CMakeLists\.txt$", f) is not None
        or re.search(r"\.cmake$", f) is not None
    )


def is_cpp_file(f) -> bool:
    return re.search(r"\.cpp$", f) is not None or re.search(r"\.hpp$", f) is not None


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


def check_license_file() -> bool:
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


def check_formatting_cmake(file) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "--check",
            file,
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

    correct_formatting = data_str == original

    return correct_formatting, None


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

    return True, None, file


def check_copyright_comments(files, pool) -> bool:
    files = [f for f in files if is_file_with_licensing_comment(f)]
    results = pool.map(check_copyright_comments_in_single_file, files)
    errors = [(output, file) for success, output, file in results if not success]
    if len(errors) > 0:
        for output, file in errors:
            print(f"Error: {file}\nIncorrect copyright comment")
            if output is not None:
                print(output)

        return False

    return True


def is_file_for_formatting(f) -> bool:
    return is_cmake_file(f) or is_cpp_file(f) or is_json_file(f) or is_python_file(f)


def check_formatting(files, pool) -> bool:
    files = [f for f in files if is_file_for_formatting(f)]
    results = pool.map(check_formatting_in_single_file, files)
    errors = [(output, file) for success, output, file in results if not success]
    if len(errors) > 0:
        for output, file in errors:
            print(
                f'Error: {file}\nIncorrect formatting; run the build in "format" mode'
            )
            if output is not None:
                print(output)

        return False

    return True


def main() -> int:
    success = check_license_file()
    if not success:
        return 1

    files = get_changed_files()
    with multiprocessing.Pool(JOBS) as pool:
        success = check_copyright_comments(files, pool)
        if not success:
            return 1

        success = check_formatting(files, pool)
        if not success:
            return 1

    return 0


if __name__ == "__main__":
    assert os.getcwd() == PROJECT_ROOT_DIR
    exit(main())
