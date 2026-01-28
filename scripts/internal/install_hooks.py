# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib
import stat

THIS_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
PROJECT_ROOT_DIR = THIS_SCRIPT_DIR.parent.parent.resolve()

GIT_DIR = PROJECT_ROOT_DIR / ".git"
PRE_COMMIT_HOOK_PATH = GIT_DIR / "hooks/pre-commit"
POST_COMMIT_HOOK_PATH = GIT_DIR / "hooks/post-commit"
POST_CHECKOUT_HOOK_PATH = GIT_DIR / "hooks/post-checkout"


def hook(script: str) -> str:
    return f"""#!/bin/bash
set -euo pipefail

THIS_SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT_DIR="$(realpath "${{THIS_SCRIPT_DIR}}/../..")"

cd "${{PROJECT_ROOT_DIR}}"

if test -f "${{PROJECT_ROOT_DIR}}/infrastructure/hooks/git/{script}";
then
  "${{PROJECT_ROOT_DIR}}/infrastructure/hooks/git/{script}"
fi
"""


PRE_COMMIT_HOOK = hook("git_pre_commit_hook")
POST_COMMIT_HOOK = hook("git_post_commit_hook")
POST_CHECKOUT_HOOK = hook("git_post_checkout_hook")


def create_hook(path: pathlib.Path, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
    path.chmod(stat.S_IRWXU)


def install_git_hooks() -> None:
    if not GIT_DIR.is_dir():
        return

    create_hook(PRE_COMMIT_HOOK_PATH, PRE_COMMIT_HOOK)
    create_hook(POST_COMMIT_HOOK_PATH, POST_COMMIT_HOOK)
    create_hook(POST_CHECKOUT_HOOK_PATH, POST_CHECKOUT_HOOK)


def main() -> int:
    install_git_hooks()

    return 0


if __name__ == "__main__":
    exit(main())
