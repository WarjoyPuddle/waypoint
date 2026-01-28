# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib
import sys

from python_imports import build_docker
from python_imports import current_timezone
from python_imports import docker_image_source_digest
from python_imports import docker_tag_exists
from python_imports import local_group_id
from python_imports import local_user_id
from python_imports import local_username
from python_imports import run_in_docker

THIS_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT_DIR = THIS_SCRIPT_DIR.resolve().parent.parent
INFRASTRUCTURE_DIR = PROJECT_ROOT_DIR / "infrastructure"
DOCKER_DIR = INFRASTRUCTURE_DIR / "docker"


def main() -> int:
    args: list[str] = [
        f"DOCKER_USERNAME={local_username()}",
        f"DOCKER_UID={local_user_id()}",
        f"DOCKER_GID={local_group_id()}",
        f"DOCKER_HOST_TIMEZONE={current_timezone()}",
    ]

    context_dir = DOCKER_DIR / "context"
    dockerfile_path = DOCKER_DIR / "build.dockerfile"
    target = "base"
    docker_tag = f"waypoint_development:{docker_image_source_digest(context_dir, dockerfile_path, args, target)}"
    if not docker_tag_exists(docker_tag):
        print("Building Docker image. This may take a long time...", flush=True)
        success = build_docker(
            docker_tag,
            dockerfile_path,
            context_dir,
            target,
            args,
        )
        if not success:
            print("Failed to build Docker image.", flush=True)

            return 1

    args: list[str] = sys.argv[1:]
    success = run_in_docker(docker_tag, PROJECT_ROOT_DIR, args)
    if not success:
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
