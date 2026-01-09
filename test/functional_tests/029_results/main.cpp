// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>
#include <functional>
#include <sstream>
#include <string>
#include <vector>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g1 = t.group("Test group 1");

  t.test(g1, "Test 1")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });

  t.test(g1, "Test 2")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });

  t.test(g1, "Test 3")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });

  auto const g2 = t.group("Test group 2");

  t.test(g2, "Test 4")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });

  t.test(g2, "Test 5")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });

  t.test(g2, "Test 6")
    .run(
      [](auto const &ctx)
      {
        ctx.assert(true, "Condition must be true");
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = run_all_tests_in_process(t);
  REQUIRE_IN_MAIN(results.success(), "Expected the run to succeed");

  auto const test_count = results.test_count();
  REQUIRE_IN_MAIN(
    test_count == 6,
    std::format("Expected test_count to be 6, but it is {}", test_count));

  std::vector const test_indices{
    3U,
    0U,
    5U,
    1U,
    2U,
    4U,
  };
  for(unsigned i = 0; i < test_count; ++i)
  {
    auto const &test_outcome = results.test_outcome(i);
    REQUIRE_IN_MAIN(
      test_outcome.test_index() == test_indices[i],
      std::format(
        "Expected test_outcome.test_index() to be {}, but it is {}",
        test_indices[i],
        test_outcome.test_index()));

    auto const group_name = std::invoke(
      [i]() -> std::string
      {
        return i < 3 ? "Test group 1" : "Test group 2";
      });
    REQUIRE_IN_MAIN(
      test_outcome.group_name() == group_name,
      std::format(
        "Expected test_outcome.group_name() to be {}, but it is {}",
        group_name,
        test_outcome.group_name()));

    auto const test_name = std::invoke(
      [i]()
      {
        std::ostringstream stream;

        stream << "Test " << i + 1;

        return stream.str();
      });
    REQUIRE_IN_MAIN(
      test_outcome.test_name() == test_name,
      std::format(
        "Expected test_outcome.test_name() to be {}, but it is {}",
        test_name,
        test_outcome.test_name()));

    auto const assertion_count = test_outcome.assertion_count();
    REQUIRE_IN_MAIN(
      assertion_count == 1,
      std::format(
        "Expected assertion_count to be 1, but it is {}",
        assertion_count));

    auto const &assertion_outcome = test_outcome.assertion_outcome(0);

    REQUIRE_IN_MAIN(
      assertion_outcome.group() == group_name,
      std::format(
        "Expected assertion_outcome.group() to be {}, but it is {}",
        group_name,
        assertion_outcome.group()));
    REQUIRE_IN_MAIN(
      assertion_outcome.test() == test_name,
      std::format(
        "Expected assertion_outcome.test() to be {}, but it is {}",
        test_name,
        assertion_outcome.test()));
    REQUIRE_STRING_EQUAL_IN_MAIN(
      assertion_outcome.message(),
      "Condition must be true",
      std::format("Unexpected string value: {}", assertion_outcome.message()));
    REQUIRE_IN_MAIN(
      assertion_outcome.passed(),
      "Expected assertion_outcome.passed() to be true");
    REQUIRE_IN_MAIN(
      assertion_outcome.index() == 0,
      std::format(
        "Expected assertion_outcome.index() to be 0, but it is {}",
        assertion_outcome.index()));
  }

  return 0;
}
