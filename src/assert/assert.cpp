// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "assert.hpp"

#include "coverage/coverage.hpp"

#include <cstdlib>
#include <iostream>
#include <source_location>
#include <string_view>

namespace waypoint::internal
{

void assert(
  bool const condition,
  std::string_view const message,
  std::source_location const loc)
{
  if(!condition)
  {
    std::cerr << "Assertion failed (waypoint)" << std::endl;
    std::cerr << "- Message: " << message << std::endl;
    std::cerr << "- File: " << loc.file_name() << " L" << loc.line() << "C"
              << loc.column() << std::endl;

    waypoint::coverage::gcov_dump();
    // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_START
    std::abort();
    // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_STOP
  }
}

} // namespace waypoint::internal
