# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os
import stat

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/../..")

GIT_DIR = os.path.realpath(f"{PROJECT_ROOT_DIR}/.git")
PRE_COMMIT_HOOK_PATH = os.path.realpath(f"{GIT_DIR}/hooks/pre-commit")
POST_COMMIT_HOOK_PATH = os.path.realpath(f"{GIT_DIR}/hooks/post-commit")
POST_CHECKOUT_HOOK_PATH = os.path.realpath(f"{GIT_DIR}/hooks/post-checkout")


def hook(script: str) -> str:
    return f"""#!/bin/sh
THIS_SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT_DIR="$(realpath "${{THIS_SCRIPT_DIR}}/../..")"

cd "${{PROJECT_ROOT_DIR}}"

if test -f "${{PROJECT_ROOT_DIR}}/scripts/internal/{script}";
then
  python3 "${{PROJECT_ROOT_DIR}}/scripts/internal/{script}"
fi
"""


PRE_COMMIT_HOOK = hook("git_pre_commit_hook.py")
POST_COMMIT_HOOK = hook("git_post_commit_hook.py")
POST_CHECKOUT_HOOK = hook("git_post_checkout_hook.py")


def create_hook(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, stat.S_IRWXU)


def install_git_hooks() -> None:
    if not os.path.isdir(GIT_DIR):
        return

    create_hook(PRE_COMMIT_HOOK_PATH, PRE_COMMIT_HOOK)
    create_hook(POST_COMMIT_HOOK_PATH, POST_COMMIT_HOOK)
    create_hook(POST_CHECKOUT_HOOK_PATH, POST_CHECKOUT_HOOK)


def main() -> int:
    install_git_hooks()

    return 0


if __name__ == "__main__":
    exit(main())
