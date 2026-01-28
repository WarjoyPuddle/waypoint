#!/bin/bash
# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

set -euo pipefail

THIS_SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT_DIR="$(realpath "${THIS_SCRIPT_DIR}/..")"

main()
{
  if test -d "${PROJECT_ROOT_DIR}/.git";
  then
    python3 -B "${PROJECT_ROOT_DIR}/scripts/internal/install_hooks.py"
  fi

  echo "Success: $(basename "$0")"
}

main
