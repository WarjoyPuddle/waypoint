#!/usr/bin/env bash
# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

THIS_SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT_DIR="$(realpath "${THIS_SCRIPT_DIR}/..")"

main()
{
  if ! python3 -B "${PROJECT_ROOT_DIR}/scripts/internal/build.py" default_static_build;
  then
    exit 1
  fi

  echo "Success: $(basename "$0")"
}

main
