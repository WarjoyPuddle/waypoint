// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>
#include <iostream>
#include <string>
#include <vector>

namespace
{

auto long_text()
{
  return std::string(1'000'000, 'X');
}

} // namespace

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g = t.group("Test group");

  t.test(g, "Test 1")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a1" << std::endl;
        ctx.assert(true);
        std::cout << "a2" << std::endl;
      });

  t.test(g, "Test 2")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a3" << std::endl;
        ctx.assert(true);
        std::cerr << "a4" << std::endl;
      });

  t.test(g, "Test 3")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cerr << "a5" << std::endl;
        ctx.assert(true);
        std::cout << "a6" << std::endl;
      });

  t.test(g, "Test 4")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cerr << "a7" << std::endl;
        ctx.assert(true);
        std::cerr << "a8" << std::endl;
      });

  t.test(g, "Test 5")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a9" << std::endl;
        std::cerr << "a10" << std::endl;
        ctx.assert(true);
        std::cout << "a11" << std::endl;
        std::cerr << "a12" << std::endl;
      });

  t.test(g, "Test 6")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a13" << std::endl;
        std::cerr << "a14" << std::endl;
        ctx.assert(true);
        std::cout << "a15" << std::endl;
        std::cerr << "a16" << std::endl;
        ctx.assert(true);
        std::cout << "a17" << std::endl;
        std::cerr << "a18" << std::endl;
      });

  t.test(g, "Test 7")
    .run(
      [](waypoint::Context const & /*ctx*/)
      {
        std::cout << "one" << std::endl;
        std::cerr << "two" << std::endl;
        std::cout << "three" << std::endl;
        std::cerr << "four" << std::endl;
        std::cout << "five" << std::endl;
        std::cerr << "six" << std::endl;
      });

  t.test(g, "Test 8")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        ctx.assert(true);
      });

  t.test(g, "Test 9")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        ctx.assert(true);
        std::cout << text << std::endl;
      });

  t.test(g, "Test 10")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        ctx.assert(true);
        std::cout << text << std::endl;
      });

  t.test(g, "Test 11")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cerr << text << std::endl;
        ctx.assert(true);
        std::cout << text << std::endl;
      });

  t.test(g, "Test 12")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        ctx.assert(true);
        std::cerr << text << std::endl;
      });

  t.test(g, "Test 13")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cerr << text << std::endl;
        ctx.assert(true);
        std::cerr << text << std::endl;
      });

  t.test(g, "Test 14")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        std::cerr << text << std::endl;
        ctx.assert(true);
        std::cout << text << std::endl;
        std::cerr << text << std::endl;
      });

  t.test(g, "Test 15")
    .run(
      [](waypoint::Context const &ctx)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        std::cerr << text << std::endl;
        ctx.assert(true);
        std::cout << text << std::endl;
        std::cerr << text << std::endl;
        ctx.assert(true);
        std::cout << text << std::endl;
        std::cerr << text << std::endl;
      });

  t.test(g, "Test 16")
    .run(
      [](waypoint::Context const & /*ctx*/)
      {
        auto const text = long_text();

        std::cout << text << std::endl;
        std::cerr << text << std::endl;
        std::cout << text << std::endl;
        std::cerr << text << std::endl;
        std::cout << text << std::endl;
        std::cerr << text << std::endl;
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = waypoint::run_all_tests(t);
  if(!results.success())
  {
    std::cerr << "Expected the run to succeed" << std::endl;

    return 1;
  }

  std::vector<std::string> const expected_std_outs = {
    "a1\na2\n",
    "a3\n",
    "a6\n",
    "",
    "a9\na11\n",
    "a13\na15\na17\n",
    "one\nthree\nfive\n",

    long_text() + "\n",
    long_text() + "\n",
    long_text() + "\n" + long_text() + "\n",
    long_text() + "\n",
    long_text() + "\n",
    "",
    long_text() + "\n" + long_text() + "\n",
    long_text() + "\n" + long_text() + "\n" + long_text() + "\n",
    long_text() + "\n" + long_text() + "\n" + long_text() + "\n",
  };
  std::vector<std::string> const expected_std_errs = {
    "",
    "a4\n",
    "a5\n",
    "a7\na8\n",
    "a10\na12\n",
    "a14\na16\na18\n",
    "two\nfour\nsix\n",
    "",
    "",
    "",
    long_text() + "\n",
    long_text() + "\n",
    long_text() + "\n" + long_text() + "\n",
    long_text() + "\n" + long_text() + "\n",
    long_text() + "\n" + long_text() + "\n" + long_text() + "\n",
    long_text() + "\n" + long_text() + "\n" + long_text() + "\n",
  };
  std::vector<std::string> const expected_test_names = {
    "Test 1",
    "Test 2",
    "Test 3",
    "Test 4",
    "Test 5",
    "Test 6",
    "Test 7",
    "Test 8",
    "Test 9",
    "Test 10",
    "Test 11",
    "Test 12",
    "Test 13",
    "Test 14",
    "Test 15",
    "Test 16",
  };

  for(unsigned i = 0; i < results.test_count(); ++i)
  {
    auto const &test_outcome = results.test_outcome(i);
    auto const *const actual_std_out = test_outcome.std_out();
    auto const *const actual_std_err = test_outcome.std_err();

    REQUIRE_STRING_EQUAL_IN_MAIN(
      test_outcome.test_name(),
      expected_test_names[i].c_str(),
      std::format("Unexpected test name {}", test_outcome.test_name()));
    REQUIRE_STRING_EQUAL_IN_MAIN(
      actual_std_out,
      expected_std_outs[i].c_str(),
      std::format("Unexpected std out in test {}", test_outcome.test_name()));
    REQUIRE_STRING_EQUAL_IN_MAIN(
      actual_std_err,
      expected_std_errs[i].c_str(),
      std::format("Unexpected std err in test {}", test_outcome.test_name()));
  }

  return 0;
}
