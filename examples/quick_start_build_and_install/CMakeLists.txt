# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

cmake_minimum_required(VERSION 4.0)

project(
  test_project
  VERSION 1.0.0
  DESCRIPTION "Test project"
  LANGUAGES CXX)

enable_testing()

# Pull Waypoint into the project
find_package(
  waypoint REQUIRED CONFIG PATHS
  ${CMAKE_CURRENT_SOURCE_DIR}/waypoint_install___/cmake NO_DEFAULT_PATH)

# Create stub library to test
add_library(the_answer_lib)
target_sources(
  the_answer_lib
  PRIVATE the_answer.cpp
  PUBLIC FILE_SET
         the_answer_lib_public_headers
         TYPE
         HEADERS
         BASE_DIRS
         ${CMAKE_CURRENT_SOURCE_DIR}
         FILES
         the_answer.hpp)
target_compile_features(the_answer_lib PRIVATE cxx_std_11)

# Create test executable
add_executable(test_program)
target_sources(test_program PRIVATE test01.cpp test02.cpp)
target_compile_features(test_program PRIVATE cxx_std_11)
target_link_libraries(
  test_program
  PRIVATE the_answer_lib
          # Waypoint is used here;
          # waypoint::waypoint_main provides its own main function
          waypoint::waypoint_main)

# Register test with ctest
add_test(NAME run_test_program COMMAND $<TARGET_FILE:test_program>)
