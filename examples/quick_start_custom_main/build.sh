#!/bin/bash
# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

set -euo pipefail

main()
{
  # Configure step
  cmake --preset configure

  # Build step
  cmake --build --preset build --config Debug

  # Run the tests with CMake
  cmake --build --preset build --target test --config Debug

  # Alternatively, run the tests with CTest (a more flexible approach)
  ctest --preset test --build-config Debug

  # You may also run the test executable directly
  build___/Debug/test_program

  echo "Success: $(basename "$0")"
}

main
