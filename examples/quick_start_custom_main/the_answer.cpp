// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "the_answer.hpp"

#include <iostream>

namespace deep_thought
{

auto the_answer() noexcept -> int
{
  std::cout << "The answer is 42" << std::endl;

  return 42;
}

} // namespace deep_thought
