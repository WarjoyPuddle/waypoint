// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#pragma once

#include "types.hpp"
#include "waypoint.hpp"

#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace waypoint
{

class TestRun;

} // namespace waypoint

namespace waypoint::internal
{

class InputPipeEnd;

class AssertionOutcome_impl
{
public:
  AssertionOutcome_impl();

  void initialize(
    TestOutcome const *test_outcome,
    std::optional<std::string> message,
    bool passed,
    unsigned long long index);

  [[nodiscard]]
  auto group_name() const -> char const *;
  [[nodiscard]]
  auto test_name() const -> char const *;
  [[nodiscard]]
  auto message() const -> std::optional<std::string> const &;
  [[nodiscard]]
  auto passed() const -> bool;
  [[nodiscard]]
  auto index() const -> unsigned long long;

private:
  TestOutcome const *test_outcome_;
  std::optional<std::string> message_;
  bool passed_;
  unsigned long long index_;
};

class TestOutcome_impl
{
public:
  TestOutcome_impl();

  void initialize(
    std::vector<std::unique_ptr<AssertionOutcome>> assertion_outcomes,
    std::string group_name,
    std::string test_name,
    unsigned long long index,
    bool disabled,
    TestOutcome::Status status,
    std::optional<unsigned long long> maybe_exit_status,
    std::string &&std_out,
    std::string &&std_err);

  [[nodiscard]]
  auto get_test_name() const -> std::string const &;
  [[nodiscard]]
  auto get_group_name() const -> std::string const &;
  [[nodiscard]]
  auto get_assertion_count() const -> unsigned long long;
  [[nodiscard]]
  auto get_assertion_outcome(unsigned long long index) const
    -> AssertionOutcome const &;
  [[nodiscard]]
  auto get_index() const -> unsigned long long;
  [[nodiscard]]
  auto disabled() const -> bool;
  [[nodiscard]]
  auto status() const -> TestOutcome::Status;
  [[nodiscard]]
  auto exit_status() const -> std::optional<unsigned long long> const &;
  [[nodiscard]]
  auto std_out() const -> std::string const &;
  [[nodiscard]]
  auto std_err() const -> std::string const &;

private:
  std::vector<std::unique_ptr<AssertionOutcome>> assertion_outcomes_;
  std::string group_name_;
  std::string test_name_;
  unsigned long long test_index_;
  bool disabled_;
  TestOutcome::Status status_;
  std::optional<unsigned long long> exit_status_;
  std::string std_out_;
  std::string std_err_;
};

class TestRecord
{
public:
  TestRecord(
    TestAssembly assembly,
    TestId test_id,
    unsigned long long timeout_ms,
    bool disabled);

  enum class Status : std::uint8_t
  {
    NotRun,
    Complete,
    Terminated,
    Timeout
  };

  [[nodiscard]]
  auto test_id() const -> TestId;
  [[nodiscard]]
  auto test_assembly() const -> TestAssembly const &;
  [[nodiscard]]
  auto disabled() const -> bool;
  [[nodiscard]]
  auto status() const -> TestRecord::Status;
  [[nodiscard]]
  auto timeout_ms() const -> unsigned long long;
  void mark_as_run();
  void mark_as_crashed();
  void mark_as_timed_out();
  void append_std_output(std::string const &text);
  void append_std_error(std::string const &text);
  auto get_std_out() const -> std::string;
  auto get_std_err() const -> std::string;

private:
  TestAssembly test_assembly_;
  TestId test_id_;
  bool disabled_;
  TestRecord::Status status_;
  unsigned long long timeout_ms_;
  std::ostringstream std_out_;
  std::ostringstream std_err_;
};

class AssertionRecord
{
public:
  AssertionRecord(
    bool condition,
    AssertionIndex index,
    std::optional<std::string> maybe_message);

  [[nodiscard]]
  auto passed() const -> bool;
  [[nodiscard]]
  auto index() const -> AssertionIndex;
  [[nodiscard]]
  auto message() const -> std::optional<std::string>;

private:
  bool condition_;
  AssertionIndex index_;
  std::optional<std::string> maybe_message_;
};

class Group_impl
{
public:
  Group_impl();

  void set_id(GroupId id);
  [[nodiscard]]
  auto get_id() const -> GroupId;

private:
  GroupId id_;
};

class Test_impl
{
public:
  ~Test_impl();
  Test_impl();
  Test_impl(Test_impl const &other) = delete;
  Test_impl(Test_impl &&other) noexcept = delete;
  auto operator=(Test_impl const &other) -> Test_impl & = delete;
  auto operator=(Test_impl &&other) noexcept -> Test_impl & = delete;

  void initialize(TestRun const &test_run, TestId id);

  [[nodiscard]]
  auto get_test_run() const -> TestRun const &;
  [[nodiscard]]
  auto get_id() const -> TestId;
  void mark_complete();

private:
  TestRun const *test_run_;
  TestId id_;
  bool incomplete_;
};

class ContextInProcess_impl
{
public:
  ContextInProcess_impl();

  void initialize(TestRun const &test_run, TestId test_id);

  [[nodiscard]]
  auto get_test_run() const -> TestRun const &;
  [[nodiscard]]
  auto generate_assertion_index() -> AssertionIndex;
  [[nodiscard]]
  auto test_id() const -> TestId;

private:
  TestRun const *test_run_;
  TestId test_id_;
  AssertionIndex assertion_index_;
};

class ContextChildProcess_impl
{
public:
  ContextChildProcess_impl();

  void initialize(
    TestRun const &test_run,
    TestId test_id,
    InputPipeEnd const &response_write_pipe,
    std::mutex &transmission_mutex);

  [[nodiscard]]
  auto get_test_run() const -> TestRun const &;
  [[nodiscard]]
  auto generate_assertion_index() -> AssertionIndex;
  [[nodiscard]]
  auto test_id() const -> TestId;
  [[nodiscard]]
  auto response_write_pipe() const -> InputPipeEnd const *;
  [[nodiscard]]
  auto transmission_mutex() const -> std::mutex *;

private:
  TestRun const *test_run_;
  TestId test_id_;
  AssertionIndex assertion_index_;
  InputPipeEnd const *response_write_pipe_;
  std::mutex *transmission_mutex_;
};

class TestRun_impl
{
public:
  TestRun_impl();

private:
  using GroupName = std::string;
  using TestName = std::string;

  enum class ErrorType : std::uint8_t
  {
    Init_DuplicateTestInGroup,
    Init_TestHasNoBody
  };

  struct Error
  {
    ErrorType type;
    std::string message;
  };

public:
  void initialize(TestRun const &test_run);
  void register_test_assembly(
    TestAssembly assembly,
    TestId test_id,
    unsigned long long timeout_ms,
    bool disabled);
  [[nodiscard]]
  auto test_records() -> std::vector<TestRecord> &;
  [[nodiscard]]
  auto generate_results() const -> TestRunResult;
  void register_assertion(
    bool condition,
    TestId test_id,
    AssertionIndex index,
    std::optional<std::string> maybe_message);
  void transmit_assertion(
    bool condition,
    TestId test_id,
    AssertionIndex index,
    std::optional<std::string> const &maybe_message,
    InputPipeEnd const &response_write_pipe) const;
  [[nodiscard]]
  auto errors() const noexcept -> std::vector<std::string>;
  [[nodiscard]]
  auto has_errors() const -> bool;
  [[nodiscard]]
  auto register_group(GroupName const &group_name) -> GroupId;
  [[nodiscard]]
  auto register_test(GroupId group_id, TestName const &test_name) -> TestId;
  [[nodiscard]]
  auto make_group(GroupId group_id) const -> Group;
  [[nodiscard]]
  auto make_test(TestId test_id) const -> Test;
  [[nodiscard]]
  auto get_group_id(TestId id) const -> GroupId;
  [[nodiscard]]
  auto get_group_id(Group const &group) const -> GroupId;
  [[nodiscard]]
  auto get_group_name(GroupId id) const -> std::string;
  [[nodiscard]]
  auto get_test_name(TestId id) const -> std::string;
  void set_test_index(TestId test_id, unsigned long long index);
  [[nodiscard]]
  auto get_test_index(TestId test_id) const -> unsigned long long;
  [[nodiscard]]
  auto test_count() const -> unsigned long long;
  [[nodiscard]]
  auto make_test_outcome(TestId test_id) const noexcept
    -> std::unique_ptr<TestOutcome>;
  void report_error(ErrorType type, std::string const &message);
  void report_duplicate_test_name(
    GroupName const &group_name,
    TestName const &test_name);
  void report_incomplete_test(TestId test_id);
  [[nodiscard]]
  auto get_passing_assertions(TestId test_id) const
    -> std::vector<AssertionRecord>;
  [[nodiscard]]
  auto get_failing_assertions(TestId test_id) const
    -> std::vector<AssertionRecord>;
  [[nodiscard]]
  auto has_failing_assertions() const -> bool;
  [[nodiscard]]
  auto make_in_process_context(TestId test_id) const
    -> std::unique_ptr<Context>;
  auto make_child_process_context(
    TestId test_id,
    InputPipeEnd const &response_write_pipe,
    std::mutex &transmission_mutex) const -> std::unique_ptr<Context>;
  void set_shuffled_test_record_ptrs();
  [[nodiscard]]
  auto get_shuffled_test_record_ptrs() const
    -> std::vector<TestRecord *> const &;
  [[nodiscard]]
  auto is_disabled(TestId test_id) const -> bool;
  void register_crashed_exit_status(
    TestId crashed_test_id,
    unsigned long long exit_status);
  auto get_crashed_exit_status(TestId test_id) const
    -> std::optional<unsigned long long>;

private:
  TestRun const *test_run_;
  GroupId group_id_counter_;
  TestId test_id_counter_;
  std::unordered_map<GroupId, GroupName> group_id2group_name_;
  std::unordered_map<TestId, TestName> test_id2test_name_;
  std::unordered_map<TestId, GroupId> test_id2group_id_;
  std::unordered_map<TestId, unsigned long long> test_id2test_index_;
  std::unordered_map<GroupId, std::unordered_set<TestName>>
    test_names_per_group_;
  std::vector<Error> errors_;
  std::unordered_map<TestId, std::vector<AssertionRecord>> passing_assertions_;
  std::unordered_map<TestId, std::vector<AssertionRecord>> failing_assertions_;
  std::vector<TestRecord> test_records_;
  std::vector<TestRecord *> shuffled_test_record_ptrs_;
  std::unordered_map<TestId, unsigned long long> crashed_exit_statuses_;
};

class TestRunResult_impl
{
public:
  TestRunResult_impl();

  void initialize(TestRun const &test_run);

  [[nodiscard]]
  auto errors() const -> std::vector<std::string> const &;
  [[nodiscard]]
  auto has_errors() const -> bool;
  [[nodiscard]]
  auto has_failing_assertions() const -> bool;
  [[nodiscard]]
  auto has_crashes() const -> bool;
  [[nodiscard]]
  auto has_timeouts() const -> bool;
  [[nodiscard]]
  auto test_outcome_count() const -> unsigned long long;
  [[nodiscard]]
  auto get_test_outcome(unsigned long long index) const -> TestOutcome const &;

private:
  bool has_failing_assertions_;
  std::vector<std::unique_ptr<TestOutcome>> test_outcomes_;
  std::vector<std::string> errors_;
};

class AutorunFunctionPtrVector_impl
{
public:
  ~AutorunFunctionPtrVector_impl();
  AutorunFunctionPtrVector_impl() noexcept;
  AutorunFunctionPtrVector_impl(AutorunFunctionPtrVector_impl const &other) =
    delete;
  AutorunFunctionPtrVector_impl(
    AutorunFunctionPtrVector_impl &&other) noexcept = delete;
  auto operator=(AutorunFunctionPtrVector_impl const &other)
    -> AutorunFunctionPtrVector_impl & = delete;
  auto operator=(AutorunFunctionPtrVector_impl &&other) noexcept
    -> AutorunFunctionPtrVector_impl & = delete;

  auto get_data() noexcept -> std::vector<AutorunFunctionPtr> &;

private:
  std::vector<AutorunFunctionPtr> data_;
};

} // namespace waypoint::internal
