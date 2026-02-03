// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g1 = t.group("Test group 1");

  t.test(g1, "Test 1")
    .run(
      [](auto const &ctx)
      {
        auto const maybe_value = waypoint::test::get_env(
          "WAYPOINT_INTERNAL_RUNNING_TEST_XTSyiOp7QMFW8P2H");
        if(ctx.assert(maybe_value.has_value()))
        {
          ctx.assert(maybe_value.value() == "123");
        }
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = run_all_tests(t);

  REQUIRE_IN_MAIN(results.success(), "Expected the run to succeed");

  auto const error_count = results.error_count();
  REQUIRE_IN_MAIN(
    error_count == 0,
    std::format("Expected error_count to be 0, but it is {}", error_count));

  auto const test_count = results.test_count();
  REQUIRE_IN_MAIN(
    test_count == 1,
    std::format("Expected test_count to be 1, but it is {}", test_count));
  auto const maybe_value =
    waypoint::test::get_env("WAYPOINT_INTERNAL_RUNNING_TEST_XTSyiOp7QMFW8P2H");
  REQUIRE_IN_MAIN(
    maybe_value.has_value(),
    "Expected maybe_value.has_value() to be true");
  REQUIRE_IN_MAIN(
    maybe_value.value() == "123",
    std::format(
      R"(Expected maybe_value.value() to be "123", but it is "{}")",
      maybe_value.value()));

  return 0;
}
