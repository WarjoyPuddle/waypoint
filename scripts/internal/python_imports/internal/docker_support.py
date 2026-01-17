# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import hashlib
import pathlib

from .process import run
from .process import run_with_output
from .system import local_username


def docker_image_source_digest(
    context_dir: pathlib.Path,
    dockerfile_path: pathlib.Path,
    args_: list[str],
    target: str,
) -> str:
    output: list[pathlib.Path] = list()
    if context_dir not in dockerfile_path.parents:
        output.append(dockerfile_path)

    for root, dirs, files in context_dir.walk():
        for f in files:
            output.append((root / f).resolve())

    output.sort()

    args = args_.copy()
    args.sort()
    args = [f"{v}\n" for v in args]

    target = target + "\n"

    digest_context = hashlib.sha3_256()

    digest_context.update("".join(args).encode("utf-8", "replace"))
    digest_context.update(target.encode("utf-8", "replace"))
    for file in output:
        with open(file, "br") as f:
            digest_context.update(f.read())

    return digest_context.hexdigest()


def docker_tag_exists(docker_tag: str) -> bool:
    success, output = run(
        [
            "docker",
            "image",
            "ls",
            "--all",
            "--format={{.Repository}}:{{.Tag}}",
            f"--filter=reference={docker_tag}",
        ]
    )

    lines = output.split("\n")
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line != ""]

    return docker_tag in lines


def build_docker(
    docker_tag: str,
    dockerfile_path: pathlib.Path,
    context_dir: pathlib.Path,
    target: str,
    args: list[str],
) -> bool:
    assert dockerfile_path.is_file()
    assert context_dir.is_dir()

    args_cli: list[str] = list()
    for arg in args:
        args_cli.append("--build-arg")
        args_cli.append(arg)

    cmd = [
        "docker",
        "build",
        "--progress",
        "plain",
        "--target",
        target,
        "--tag",
        docker_tag,
        "--file",
        str(dockerfile_path),
    ]
    cmd += args_cli
    cmd += [str(context_dir)]

    success, output = run(cmd)
    if not success:
        if output is not None:
            print(output)

        return False

    return True


def run_in_docker(
    docker_tag: str, host_workspace_dir: pathlib.Path, command: list[str]
) -> bool:
    workdir_in_container = pathlib.Path("/workspace")

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--tty",
        "--user",
        local_username(),
        "--volume",
        f"{host_workspace_dir}:{workdir_in_container}",
        "--workdir",
        workdir_in_container,
        docker_tag,
    ]
    docker_cmd += command

    success = run_with_output(docker_cmd)

    return success
