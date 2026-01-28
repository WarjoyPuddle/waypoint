// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#pragma once

#include <memory>
#include <optional>
#include <string>
#include <utility>

namespace waypoint::internal
{

class Response
{
public:
  enum class Code : unsigned char
  {
    Invalid,
    Ready,
    Assertion,
    TestComplete,
    ShuttingDown,
    Timeout
  };

  Response(
    Code code_,
    unsigned long long test_id_,
    bool assertion_passed_,
    unsigned long long assertion_index_,
    std::optional<std::string> assertion_message_);

  Code code;
  unsigned long long test_id;
  bool assertion_passed;
  unsigned long long assertion_index;
  std::optional<std::string> assertion_message;
};

class Command
{
public:
  enum class Code : unsigned char
  {
    Invalid,
    Attention,
    RunTest,
    End
  };

  Code code;
  unsigned long long test_index;
};

class InputPipeEnd_impl;

class InputPipeEnd
{
public:
  ~InputPipeEnd();
  explicit InputPipeEnd(InputPipeEnd_impl *impl);
  InputPipeEnd(InputPipeEnd const &other) = delete;
  InputPipeEnd(InputPipeEnd &&other) noexcept;
  auto operator=(InputPipeEnd const &other) -> InputPipeEnd & = delete;
  auto operator=(InputPipeEnd &&other) noexcept -> InputPipeEnd & = delete;

  void write(unsigned char const *buffer, unsigned long long count) const;

private:
  std::unique_ptr<InputPipeEnd_impl> impl_;
};

class OutputPipeEnd_impl;

class OutputPipeEnd
{
public:
  enum class ReadResult : unsigned char
  {
    Success,
    PipeClosed
  };

  ~OutputPipeEnd();
  explicit OutputPipeEnd(OutputPipeEnd_impl *impl);
  OutputPipeEnd(OutputPipeEnd const &other) = delete;
  OutputPipeEnd(OutputPipeEnd &&other) noexcept;
  auto operator=(OutputPipeEnd const &other) -> OutputPipeEnd & = delete;
  auto operator=(OutputPipeEnd &&other) noexcept -> OutputPipeEnd & = delete;

  [[nodiscard]]
  auto read_exactly(unsigned char *buffer, unsigned long long count) const
    -> ReadResult;

private:
  std::unique_ptr<OutputPipeEnd_impl> impl_;
};

class ChildProcess_impl;

class ChildProcess
{
public:
  ~ChildProcess();
  ChildProcess();
  ChildProcess(ChildProcess const &other) = delete;
  ChildProcess(ChildProcess &&other) noexcept = delete;
  auto operator=(ChildProcess const &other) -> ChildProcess & = delete;
  auto operator=(ChildProcess &&other) noexcept -> ChildProcess & = delete;

  [[nodiscard]]
  auto command_write_pipe() const -> InputPipeEnd const &;
  [[nodiscard]]
  auto response_read_pipe() const -> OutputPipeEnd const &;

  [[nodiscard]]
  auto wait() const -> unsigned long long;

private:
  std::unique_ptr<ChildProcess_impl const> impl_;
};

[[nodiscard]]
auto get_pipes_from_env() noexcept -> std::pair<OutputPipeEnd, InputPipeEnd>;
[[nodiscard]]
auto is_child() -> bool;

} // namespace waypoint::internal
