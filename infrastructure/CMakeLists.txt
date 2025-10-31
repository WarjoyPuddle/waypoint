# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

cmake_minimum_required(VERSION 4.0)

project(
  project_waypoint
  VERSION 0.0.1
  DESCRIPTION "Lightweight C++ unit testing framework"
  LANGUAGES CXX)

enable_testing()

option(BUILD_SHARED_LIBS "Build shared libraries" FALSE)

include(${CMAKE_CURRENT_SOURCE_DIR}/tools.cmake)

new_platform_specific_internal_library(
  TARGET
  coverage
  DIRECTORY
  src/coverage
  SOURCES
  coverage.cpp
  PUBLIC_HEADERS
  coverage.hpp)

new_internal_library(
  TARGET
  assert
  DIRECTORY
  src/assert
  SOURCES
  assert.cpp
  PUBLIC_HEADERS
  assert.hpp
  PRIVATE_LINKS
  coverage)

new_platform_specific_internal_library(
  TARGET
  process
  DIRECTORY
  src/process
  SOURCES
  process.cpp
  PUBLIC_HEADERS
  process.hpp
  PRIVATE_LINKS
  assert
  coverage)

new_implementation_library(
  TARGET
  waypoint_impl
  DIRECTORY
  src/waypoint
  INCLUDE_PREFIX
  waypoint
  SOURCES
  function.cpp
  impls.cpp
  registrar.cpp
  smart_ptrs.cpp
  waypoint.cpp
  PUBLIC_HEADERS
  waypoint.hpp
  PRIVATE_HEADERS
  impls.hpp
  types.hpp
  PRIVATE_LINKS
  coverage
  process)

new_implementation_library(
  TARGET
  waypoint_main_impl
  DIRECTORY
  src/waypoint
  SOURCES
  entry_point.cpp
  PUBLIC_LINKS
  waypoint_impl)

new_exported_library(TARGET waypoint INTERFACE_LINKS waypoint_impl)

new_exported_library(TARGET waypoint_main INTERFACE_LINKS waypoint_main_impl)

if(DEFINED PRESET_BUILD_WAYPOINT_TESTS_jsGLwkD9eVN5hzRr
   AND PRESET_BUILD_WAYPOINT_TESTS_jsGLwkD9eVN5hzRr)
  add_custom_target(all_tests)

  new_test_library(
    TARGET
    test_helpers
    DIRECTORY
    test/test_helpers
    SOURCES
    test_helpers.cpp
    test_helpers_crash.cpp
    PUBLIC_HEADERS
    test_helpers.hpp
    PRIVATE_HEADERS
    test_helpers_crash.hpp
    PRIVATE_LINKS
    coverage
    waypoint_impl)

  new_basic_test(000_include_only)
  new_basic_test(001_init_only)
  new_basic_test(002_empty_autorun_block_with_init)
  new_basic_test(003_two_empty_autoruns_with_init)
  new_basic_test(004_empty_autorun_block_no_init)
  new_basic_test(005_two_empty_autoruns_no_init)
  new_basic_test(006_one_empty_group)
  new_basic_test(007_two_empty_groups_diff_names)
  new_basic_test(008_two_empty_groups_same_name)
  new_basic_test(009_trivial_test)
  new_basic_test(010_two_tests_same_group_diff_name)
  new_basic_test(011_two_tests_diff_group_diff_name)
  new_basic_test(012_two_tests_diff_group_same_name)
  new_basic_test(013_two_tests_same_group_same_name)
  new_basic_test(014_passing_test)
  new_basic_test(015_failing_test)
  new_basic_test(016_passing_test_with_auto)
  new_basic_test(017_failing_test_with_auto)
  new_basic_test(018_failing_test_with_auto)
  new_basic_test(019_failing_test_with_auto)
  new_basic_test(020_failing_test_with_auto)
  new_basic_test(021_failing_test_with_auto)
  new_basic_test(022_failing_test_with_auto)
  new_basic_test(023_failing_test_with_auto)
  new_basic_test(024_failing_test_with_auto)
  new_basic_test(025_failing_test_with_auto)
  new_basic_test(026_multiple_tests)

  new_impl_test(027_internal_smart_ptrs)

  new_basic_test(028_assertion_messages)
  new_basic_test(029_results)
  new_basic_test(030_capturing_lambda_as_test_body)
  new_basic_test(031_mutable_lambda_as_test_body)
  new_basic_test(032_setup)
  new_basic_test(033_teardown)
  new_basic_test(034_incomplete_tests)
  new_basic_test(035_assume)
  new_basic_test(036_disable)
  new_basic_test(037_status)
  new_basic_test(038_process)
  new_basic_test(039_process)
  new_basic_test(040_process)

  new_basic_test(041_init_only)
  new_basic_test(042_empty_autorun_block_with_init)
  new_basic_test(043_two_empty_autoruns_with_init)
  new_basic_test(044_one_empty_group)
  new_basic_test(045_two_empty_groups_diff_names)
  new_basic_test(046_two_empty_groups_same_name)
  new_basic_test(047_trivial_test)
  new_basic_test(048_two_tests_same_group_diff_name)
  new_basic_test(049_two_tests_diff_group_diff_name)
  new_basic_test(050_two_tests_diff_group_same_name)
  new_basic_test(051_two_tests_same_group_same_name)
  new_basic_test(052_passing_test)
  new_basic_test(053_failing_test)
  new_basic_test(054_passing_test_with_auto)
  new_basic_test(055_failing_test_with_auto)
  new_basic_test(056_failing_test_with_auto)
  new_basic_test(057_failing_test_with_auto)
  new_basic_test(058_failing_test_with_auto)
  new_basic_test(059_failing_test_with_auto)
  new_basic_test(060_failing_test_with_auto)
  new_basic_test(061_failing_test_with_auto)
  new_basic_test(062_failing_test_with_auto)
  new_basic_test(063_failing_test_with_auto)
  new_basic_test(064_multiple_tests)
  new_basic_test(065_assertion_messages)
  new_basic_test(066_results)
  new_basic_test(067_capturing_lambda_as_test_body)
  new_basic_test(068_mutable_lambda_as_test_body)
  new_basic_test(069_setup)
  new_basic_test(070_teardown)
  new_basic_test(071_incomplete_tests)
  new_basic_test(072_assume)
  new_basic_test(073_disable)
  new_basic_test(074_status)
  new_basic_test(075_env_vars)
  new_basic_test(076_crash)
  new_basic_test(077_crash)
  new_basic_test(078_crash)
  new_basic_test(079_crash)
  new_basic_test(080_crash)
  new_basic_test(081_crash)
  new_basic_test(082_crash)
  new_basic_test(083_crash)
  new_basic_test(084_timeout)
  new_basic_test(085_timeout)
  new_basic_test(086_timeout)
  new_basic_test(087_timeout)
  new_basic_test(088_timeout)
  new_basic_test(089_process_exit_status)

  new_impl_test(090_assert)

  new_cxx_std_11_test(091_cxx_std_11)

  new_multifile_test(092_multifile_test)

  new_waypoint_main_test(TARGET 093_waypoint_main_pass)
  new_waypoint_main_test(EXPECTED_FAILURE TARGET 094_waypoint_main_fail)
  new_waypoint_main_test(EXPECTED_FAILURE TARGET 095_waypoint_main_error)
endif()

prepare_installation()
