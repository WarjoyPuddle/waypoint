# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import pathlib

from .cmake import build_dir_from_preset
from .file_types import is_cpp_file
from .file_types import is_cpp_source_file
from .process import run


def find_files_by_name(dir_path: pathlib.Path, pred) -> list[pathlib.Path]:
    assert dir_path.is_dir()

    with contextlib.chdir(dir_path):
        success1, output1 = run(["git", "ls-files", "--exclude-standard", "--cached"])
        success2, output2 = run(["git", "ls-files", "--exclude-standard", "--other"])
        if not (success1 and success2):
            return find_files_by_name_fallback(dir_path, pred)

    lines = output1.split("\n")
    lines += output2.split("\n")
    lines = [line.strip() for line in lines]
    paths = [dir_path / line for line in lines if line != ""]
    paths = [path for path in paths if path.is_file() and pred(path)]

    paths = list(set(paths))

    paths.sort()

    if len(paths) == 0:
        return find_files_by_name_fallback(dir_path, pred)

    return paths


def find_files_by_name_fallback(dir_path: pathlib.Path, pred) -> list[pathlib.Path]:
    output: list[pathlib.Path] = list()
    for root, dirs, files in dir_path.walk():
        indices_to_remove = []
        for i, d in enumerate(dirs):
            if d.startswith("."):
                indices_to_remove.append(i)
                continue
            if "___" in d:
                indices_to_remove.append(i)
                continue
        indices_to_remove.sort(reverse=True)
        for i in indices_to_remove:
            dirs.pop(i)

        indices_to_remove = []
        for i, f in enumerate(files):
            if "___" in f:
                indices_to_remove.append(i)
                continue
        indices_to_remove.sort(reverse=True)
        for i in indices_to_remove:
            files.pop(i)

        for f in files:
            path = (root / f).resolve()
            if pred(path):
                output.append(path)

    output.sort()

    return output


def find_all_files(root_dir: pathlib.Path) -> list[pathlib.Path]:
    return find_files_by_name(root_dir, lambda x: True)


def invert_index(index) -> dict[pathlib.Path, set[pathlib.Path]]:
    output: dict[pathlib.Path, set[pathlib.Path]] = {}
    for file in index.keys():
        deps = index[file]
        for d in deps:
            if d not in output.keys():
                output[d] = set()
            output[d].add(file)
            output[d].add(d)

    return output


def process_depfiles(
    depfile_paths: list[pathlib.Path], root_dir: pathlib.Path
) -> dict[pathlib.Path, set[pathlib.Path]]:
    index: dict[pathlib.Path, set[pathlib.Path]] = dict()
    for path in depfile_paths:
        with open(path, "r") as f:
            lines = f.readlines()
        lines = lines[1:]
        lines = [line.lstrip(" ").rstrip(" \\\n") for line in lines]
        paths: list[pathlib.Path] = list()
        for line in lines:
            for x in line.split(" "):
                paths.append(pathlib.Path(x))

        paths = [p.resolve() for p in paths if p.is_file() and root_dir in p.parents]

        cpp_file = paths[0]

        if cpp_file not in index.keys():
            index[cpp_file]: set[pathlib.Path] = set()

        index[cpp_file].update(paths)

    return index


def get_files_staged_for_commit(root_dir: pathlib.Path) -> list[pathlib.Path]:
    with contextlib.chdir(root_dir):
        run(["git", "update-index", "--really-refresh", "-q"])
        success, output = run(["git", "diff-index", "--cached", "--name-only", "HEAD"])
        assert (
            success
        ), "Failed to call Git; ensure you are in a Git repository and that Git is installed."

    files = output.strip().split("\n")
    out: set[pathlib.Path] = set()
    for f in files:
        path = (root_dir / f.strip()).resolve()
        if path.is_file():
            out.add(path)

    out2 = list(out)
    out2.sort()

    return out2


def get_changed_files(root_dir: pathlib.Path, predicate) -> list[pathlib.Path]:
    with contextlib.chdir(root_dir):
        run(["git", "update-index", "--really-refresh", "-q"])
        # List untracked+unstaged files
        success1, output1 = run(["git", "ls-files", "--others", "--exclude-standard"])
        # List all changes except untracked+unstaged
        success2, output2 = run(["git", "diff-index", "--name-only", "HEAD"])
        # Fall back to all files if git is not available
        assert (
            success1 and success2
        ), "Failed to call Git; ensure you are in a Git repository and that Git is installed."

        files = output1.strip().split("\n")
        files += output2.strip().split("\n")
        out: set[pathlib.Path] = set()
        for f in files:
            path = (root_dir / f.strip()).resolve()
            if path.is_file() and predicate(path):
                out.add(path)

        out2 = list(out)
        out2.sort()

        return out2


def collect_depfiles(preset, cmake_source_dir: pathlib.Path) -> list[pathlib.Path]:
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    depfiles: list[pathlib.Path] = []
    for root, dirs, files in build_dir.walk():
        for f in files:
            depfiles.append(root / f)
    depfiles = [
        f.resolve() for f in depfiles if f.is_file() and f.suffixes[-2:] == [".o", ".d"]
    ]
    depfiles.sort()

    return depfiles


def changed_cpp_source_files_and_dependents(
    root_dir: pathlib.Path, cmake_source_dir: pathlib.Path, preset
) -> list[pathlib.Path]:
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


def find_all_cpp_source_files(root_dir: pathlib.Path) -> list[pathlib.Path]:
    return find_files_by_name(root_dir, is_cpp_source_file)
