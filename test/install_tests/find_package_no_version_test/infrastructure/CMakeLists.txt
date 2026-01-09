# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

cmake_minimum_required(VERSION 4.0)

project(
  project_waypoint_find_package_no_version_test
  VERSION 1.0.0
  DESCRIPTION "Test project for loading waypoint with find_package (no version)"
  LANGUAGES CXX)

enable_testing()

set(PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw ${CMAKE_CURRENT_SOURCE_DIR}/..)

find_package(
  waypoint REQUIRED CONFIG PATHS
  ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/${PRESET_WAYPOINT_INSTALL_DIR}/cmake
  NO_DEFAULT_PATH)

add_library(stub_library STATIC)
target_sources(
  stub_library
  PRIVATE ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/src/stub_library/stub_library.cpp
)
target_sources(
  stub_library
  INTERFACE
    FILE_SET
    stub_library_interface_headers
    TYPE
    HEADERS
    BASE_DIRS
    ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/src/stub_library/include
    FILES
    ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/src/stub_library/include/stub_library/stub_library.hpp
)
target_sources(
  stub_library
  PRIVATE
    FILE_SET
    stub_library_own_headers
    TYPE
    HEADERS
    BASE_DIRS
    ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/src/stub_library/include/stub_library
    FILES
    ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/src/stub_library/include/stub_library/stub_library.hpp
)

target_compile_features(
  stub_library
  PRIVATE cxx_std_11
  PUBLIC cxx_std_11)
set_target_properties(stub_library PROPERTIES COMPILE_WARNING_AS_ERROR TRUE)
set_target_properties(stub_library PROPERTIES LINK_WARNING_AS_ERROR TRUE)
set_target_properties(stub_library PROPERTIES CXX_EXTENSIONS FALSE)
set_target_properties(stub_library PROPERTIES EXPORT_COMPILE_COMMANDS TRUE)

add_custom_target(all_tests)

add_executable(find_package_no_version_test)
add_dependencies(all_tests find_package_no_version_test)
set_target_properties(find_package_no_version_test PROPERTIES EXCLUDE_FROM_ALL
                                                              TRUE)
target_sources(
  find_package_no_version_test
  PRIVATE
    ${PROJECT_ROOT_DIR_n6kbMY9gioYgo9jw}/test/find_package_no_version_test/main.cpp
)
target_link_libraries(find_package_no_version_test
                      PRIVATE stub_library waypoint::waypoint_no_main)

add_test(NAME test_find_package_no_version_test
         COMMAND $<TARGET_FILE:find_package_no_version_test>)
set_tests_properties(test_find_package_no_version_test PROPERTIES LABELS test)

target_compile_features(find_package_no_version_test PRIVATE cxx_std_11)
set_target_properties(find_package_no_version_test
                      PROPERTIES COMPILE_WARNING_AS_ERROR TRUE)
set_target_properties(find_package_no_version_test
                      PROPERTIES LINK_WARNING_AS_ERROR TRUE)
set_target_properties(find_package_no_version_test PROPERTIES CXX_EXTENSIONS
                                                              FALSE)
set_target_properties(find_package_no_version_test
                      PROPERTIES EXPORT_COMPILE_COMMANDS TRUE)

function(switch_stdlib_for_clang target)
  if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    target_compile_options(${target} PRIVATE -stdlib=libc++)
    target_link_options(${target} PRIVATE -lc++)
  endif()
endfunction()

switch_stdlib_for_clang(stub_library)
switch_stdlib_for_clang(find_package_no_version_test)
