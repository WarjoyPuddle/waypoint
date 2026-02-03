// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>
#include <vector>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g1 = t.group("Test group 1");

  t.test(g1, "Test 1")
    .run(
      [](auto const &ctx)
      {
        if(ctx.assert(true, "message 1"))
        {
          ctx.assert(false, "message 2");

          if(!ctx.assert(true, "message 3"))
          {
            ctx.assert(false, "message 4");

            return;
          }

          ctx.assert(false, "message 5");
          ctx.assert(true, "message 6");

          if(!ctx.assert(false))
          {
            ctx.assert(false, "message 7");
            ctx.assert(true, "message 8");

            return;
          }

          ctx.assert(true, "message 9");
        }
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = run_all_tests_in_process(t);

  REQUIRE_IN_MAIN(!results.success(), "Expected the run to fail");

  auto const error_count = results.error_count();
  REQUIRE_IN_MAIN(
    error_count == 0,
    std::format("Expected error_count to be 0, but it is {}", error_count));

  auto const test_count = results.test_count();
  REQUIRE_IN_MAIN(
    test_count == 1,
    std::format("Expected test_count to be 1, but it is {}", test_count));

  auto const &test_outcome = results.test_outcome(0);
  auto const assertion_count = test_outcome.assertion_count();
  REQUIRE_IN_MAIN(
    assertion_count == 8,
    std::format(
      "Expected assertion_count to be 8, but it is {}",
      assertion_count));

  for(unsigned i = 0; i < assertion_count; ++i)
  {
    auto const &assertion_outcome = test_outcome.assertion_outcome(i);
    std::vector<char const *> messages = {
      "message 1",
      "message 2",
      "message 3",
      "message 5",
      "message 6",
      nullptr,
      "message 7",
      "message 8"};

    char const *actual_message = assertion_outcome.message();
    char const *expected_message = messages[i];
    if(expected_message == nullptr)
    {
      REQUIRE_IN_MAIN(
        actual_message == nullptr,
        "Expected actual_message == nullptr");
    }
    else
    {
      REQUIRE_STRING_EQUAL_IN_MAIN(
        actual_message,
        expected_message,
        std::format("Unexpected string value: {}", actual_message));
    }

    std::vector const expected_outcomes =
      {true, false, true, false, true, false, false, true};
    auto const expected_outcome = expected_outcomes[i];
    auto const actual_outcome = assertion_outcome.passed();

    REQUIRE_IN_MAIN(
      actual_outcome == expected_outcome,
      std::format(
        "Expected actual_outcome to be {}, but it is {}",
        expected_outcome,
        actual_outcome));
  }

  return 0;
}
