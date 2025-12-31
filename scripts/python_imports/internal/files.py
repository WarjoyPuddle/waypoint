# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import os
import re
import typing

from .cmake import build_dir_from_preset
from .file_types import is_cpp_file
from .file_types import is_cpp_source_file
from .process import run


def find_files_by_name(dir_path, pred) -> typing.List[str]:
    output = []
    for root, dirs, files in os.walk(dir_path):
        indices_to_remove = []
        for i, d in enumerate(dirs):
            if d.startswith("."):
                indices_to_remove.append(i)
                continue
            if d.startswith("_"):
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
            if f.startswith("_"):
                if f != "__init__.py":
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


def find_all_files(root_dir) -> typing.List[str]:
    return find_files_by_name(root_dir, lambda x: True)


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


def process_depfiles(depfile_paths, root_dir) -> typing.Dict[str, typing.Set[str]]:
    index = {}
    for path in depfile_paths:
        with open(path, "r") as f:
            lines = f.readlines()
        lines = lines[1:]
        lines = [line.lstrip(" ").rstrip(" \\\n") for line in lines]
        paths = []
        for line in lines:
            if " " in line:
                for x in line.split(" "):
                    paths.append(x)
                continue
            paths.append(line)

        paths = [os.path.realpath(p) for p in paths if os.path.isfile(p)]
        paths = [p for p in paths if p.startswith(f"{root_dir}/")]

        cpp_file = paths[0]

        if cpp_file not in index.keys():
            index[cpp_file] = set()

        index[cpp_file].update(paths)

    return index


def get_files_staged_for_commit(root_dir) -> typing.List[str]:
    # TODO: update to contextlib.chdir after upgrade
    assert os.getcwd() == root_dir

    success, output = run(["git", "diff", "--cached", "--name-only"])
    if not success:
        return find_all_files(root_dir)

    files = output.strip().split("\n")
    out = []
    for f in files:
        path = os.path.realpath(f"{root_dir}/{f.strip()}")
        if os.path.isfile(path):
            out.append(path)

    out.sort()

    return out


def get_changed_files(root_dir, predicate) -> typing.List[str]:
    with contextlib.chdir(root_dir):
        success1, output1 = run(["git", "diff", "--name-only"])
        success2, output2 = run(["git", "diff", "--cached", "--name-only"])
        success3, output3 = run(["git", "ls-files", "--others", "--exclude-standard"])
        # Fall back to all files if git is not available
        if not (success1 and success2 and success3):
            return find_files_by_name(root_dir, predicate)

        files = output1.strip().split("\n")
        files += output2.strip().split("\n")
        files += output3.strip().split("\n")
        out = []
        for f in files:
            path = os.path.realpath(f"{root_dir}/{f.strip()}")
            if os.path.isfile(path) and predicate(path):
                out.append(path)

        out = list(set(out))
        out.sort()

        return out


def collect_depfiles(preset, cmake_source_dir):
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
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


def changed_cpp_source_files_and_dependents(
    root_dir, cmake_source_dir, preset
) -> typing.List[str]:
    changed_cpp_files = get_changed_files(root_dir, is_cpp_file)
    if len(changed_cpp_files) == 0:
        return []

    depfiles = collect_depfiles(preset, cmake_source_dir)
    index = process_depfiles(depfiles, root_dir)
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


def find_all_cpp_source_files(root_dir) -> typing.List[str]:
    return find_files_by_name(root_dir, is_cpp_source_file)
