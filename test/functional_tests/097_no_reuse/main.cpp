// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g = t.group("Test group");

  t.test(g, "Test 1")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(true);
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results1 = waypoint::run_all_tests(t);
  REQUIRE_IN_MAIN(results1.success(), "Expected the run to succeed");

  REQUIRE_IN_MAIN(results1.error_count() == 0, "Expected no errors");

  auto const results2 = waypoint::run_all_tests(t);
  REQUIRE_IN_MAIN(!results2.success(), "Expected the run to fail");

  REQUIRE_IN_MAIN(results2.error_count() == 1, "Expected one error");
  REQUIRE_STRING_EQUAL_IN_MAIN(
    results2.error(0),
    "Instance of waypoint::TestRun cannot be reused",
    std::format("Unexpected error message: {}", results2.error(0)));

  return 0;
}
