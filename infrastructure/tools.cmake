# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

include_guard(GLOBAL)

macro(add_to_all_tests)
  if(TARGET all_tests)
    add_dependencies(all_tests ${arg_TARGET})
  endif()
endmacro()

macro(define_tests)
  add_test(NAME test_${arg_TARGET} COMMAND $<TARGET_FILE:${arg_TARGET}>)
  set_tests_properties(test_${arg_TARGET} PROPERTIES LABELS test)
  set_tests_properties(
    test_${arg_TARGET}
    PROPERTIES ENVIRONMENT WAYPOINT_INTERNAL_RUNNING_TEST_XTSyiOp7QMFW8P2H=123)

  if(DEFINED arg_EXPECTED_FAILURE AND arg_EXPECTED_FAILURE)
    set_tests_properties(test_${arg_TARGET} PROPERTIES WILL_FAIL TRUE)
  endif()

  add_test(
    NAME valgrind_${arg_TARGET}
    COMMAND valgrind --leak-check=yes --error-exitcode=1
            $<TARGET_FILE:${arg_TARGET}>
    CONFIGURATIONS Debug)
  set_tests_properties(valgrind_${arg_TARGET} PROPERTIES LABELS valgrind)
  set_tests_properties(
    valgrind_${arg_TARGET}
    PROPERTIES ENVIRONMENT WAYPOINT_INTERNAL_RUNNING_TEST_XTSyiOp7QMFW8P2H=123)

  if(DEFINED arg_EXPECTED_FAILURE AND arg_EXPECTED_FAILURE)
    set_tests_properties(valgrind_${arg_TARGET} PROPERTIES WILL_FAIL TRUE)
  endif()
endmacro()

macro(links_and_sources)
  if(DEFINED arg_SOURCES)
    target_sources(${arg_TARGET} PRIVATE ${arg_SOURCES})
  endif()

  if(DEFINED arg_PRIVATE_LINKS)
    target_link_libraries(${arg_TARGET} PRIVATE ${arg_PRIVATE_LINKS})
  endif()
  if(DEFINED arg_PUBLIC_LINKS)
    target_link_libraries(${arg_TARGET} PUBLIC ${arg_PUBLIC_LINKS})
  endif()
endmacro()

macro(interface_links)
  if(DEFINED arg_INTERFACE_LINKS)
    target_link_libraries(${arg_TARGET} INTERFACE ${arg_INTERFACE_LINKS})
  endif()
endmacro()

macro(exclude_from_all)
  set_target_properties(${arg_TARGET} PROPERTIES EXCLUDE_FROM_ALL TRUE)
endmacro()

macro(do_not_install_public_headers)
  header_file_sets_and_libraries()

  if(DEFINED arg_PUBLIC_HEADERS)
    target_link_libraries(
      ${arg_TARGET}
      PUBLIC $<BUILD_LOCAL_INTERFACE:library_interface_headers_${arg_TARGET}>
      PRIVATE $<BUILD_LOCAL_INTERFACE:library_own_headers_${arg_TARGET}>)
  endif()
endmacro()

macro(install_public_headers)
  header_file_sets_and_libraries()

  if(DEFINED arg_PUBLIC_HEADERS)
    target_link_libraries(
      ${arg_TARGET}
      PUBLIC library_interface_headers_${arg_TARGET}
      PRIVATE $<BUILD_LOCAL_INTERFACE:library_own_headers_${arg_TARGET}>)
  endif()
endmacro()

macro(conditionally_enable_pic)
  if(BUILD_SHARED_LIBS)
    set_target_properties(${arg_TARGET} PROPERTIES POSITION_INDEPENDENT_CODE
                                                   TRUE)
  endif()
endmacro()

macro(standard_presets)
  if(DEFINED PRESET_ELEVATED_COMPILER_WARNINGS)
    separate_arguments(PRESET_ELEVATED_COMPILER_WARNINGS)
    target_compile_options(${arg_TARGET}
                           PRIVATE ${PRESET_ELEVATED_COMPILER_WARNINGS})
  endif()

  if(DEFINED PRESET_PROP_COMPILE_WARNING_AS_ERROR)
    set_target_properties(
      ${arg_TARGET} PROPERTIES COMPILE_WARNING_AS_ERROR
                               ${PRESET_PROP_COMPILE_WARNING_AS_ERROR})
  endif()

  if(DEFINED PRESET_PROP_LINK_WARNING_AS_ERROR)
    set_target_properties(
      ${arg_TARGET} PROPERTIES LINK_WARNING_AS_ERROR
                               ${PRESET_PROP_LINK_WARNING_AS_ERROR})
  endif()

  if(DEFINED PRESET_PROP_CXX_EXTENSIONS)
    set_target_properties(
      ${arg_TARGET} PROPERTIES CXX_EXTENSIONS ${PRESET_PROP_CXX_EXTENSIONS})
  endif()

  if(DEFINED PRESET_PROP_EXPORT_COMPILE_COMMANDS)
    set_target_properties(
      ${arg_TARGET} PROPERTIES EXPORT_COMPILE_COMMANDS
                               ${PRESET_PROP_EXPORT_COMPILE_COMMANDS})
  endif()
endmacro()

macro(conditionally_enable_coverage)
  if(DEFINED PRESET_ENABLE_COVERAGE)
    target_compile_options(${arg_TARGET} PRIVATE ${PRESET_ENABLE_COVERAGE})
    target_link_options(${arg_TARGET} PRIVATE ${PRESET_ENABLE_COVERAGE})

    target_compile_definitions(
      ${arg_TARGET} PRIVATE WAYPOINT_INTERNAL_COVERAGE_IOm5lSCCB6p0j19)
  endif()
endmacro()

macro(disable_exceptions_in_coverage_mode)
  if(DEFINED PRESET_ENABLE_COVERAGE)
    target_compile_options(${arg_TARGET} PRIVATE -fno-exceptions)
  endif()
endmacro()

macro(conditionally_enable_address_sanitizer)
  if(DEFINED PRESET_USE_ADDRESS_SANITIZER_Yc27ZqrRDoMnuQXw)
    target_compile_options(
      ${arg_TARGET} PRIVATE -fsanitize=address -g -fno-omit-frame-pointer
                            -fno-inline-functions -fno-optimize-sibling-calls)
    target_link_options(${arg_TARGET} PRIVATE -fsanitize=address -g)
  endif()
endmacro()

macro(conditionally_enable_undefined_behaviour_sanitizer)
  if(DEFINED PRESET_USE_UNDEFINED_BEHAVIOUR_SANITIZER_Sg9fNtkF8wHdPaeP)
    target_compile_options(
      ${arg_TARGET}
      PRIVATE -g
              -fsanitize=undefined
              -fsanitize=bounds
              -fsanitize=float-divide-by-zero
              -fsanitize=implicit-conversion
              -fsanitize=integer
              -fsanitize=nullability
              -fsanitize=vptr
              -fno-sanitize=unsigned-integer-overflow
              -fno-sanitize-recover=all)
    target_link_options(
      ${arg_TARGET}
      PRIVATE
      -g
      -fsanitize=undefined
      -fsanitize=bounds
      -fsanitize=float-divide-by-zero
      -fsanitize=implicit-conversion
      -fsanitize=integer
      -fsanitize=nullability
      -fsanitize=vptr
      -fno-sanitize-recover=all)
  endif()
endmacro()

macro(header_file_sets_and_libraries)
  if(NOT DEFINED arg_TARGET OR NOT DEFINED arg_DIRECTORY)
    message(FATAL_ERROR "header_file_sets_and_libraries error")
  endif()

  if(DEFINED arg_PRIVATE_HEADERS)
    target_sources(
      ${arg_TARGET}
      PRIVATE FILE_SET
              internal_headers_${arg_TARGET}
              TYPE
              HEADERS
              BASE_DIRS
              ${arg_DIRECTORY}/internal
              FILES
              ${arg_PRIVATE_HEADERS})
  endif()

  if(DEFINED arg_PUBLIC_HEADERS)
    if(NOT DEFINED arg_INCLUDE_PREFIX)
      set(arg_INCLUDE_PREFIX ${arg_TARGET})
    endif()

    add_library(library_own_headers_${arg_TARGET} INTERFACE)
    target_sources(
      library_own_headers_${arg_TARGET}
      INTERFACE FILE_SET
                own_headers_${arg_TARGET}
                TYPE
                HEADERS
                BASE_DIRS
                ${arg_DIRECTORY}/include/${arg_INCLUDE_PREFIX}
                FILES
                ${arg_PUBLIC_HEADERS})

    add_library(library_interface_headers_${arg_TARGET} INTERFACE)
    target_sources(
      library_interface_headers_${arg_TARGET}
      INTERFACE FILE_SET
                interface_headers_${arg_TARGET}
                TYPE
                HEADERS
                BASE_DIRS
                ${arg_DIRECTORY}/include
                FILES
                ${arg_PUBLIC_HEADERS})
  endif()
endmacro()

macro(prepare_paths)
  set(PROJECT_ROOT_DIR_iUj6dGn1gNrOcYQ7 ${CMAKE_CURRENT_SOURCE_DIR}/..)

  if(DEFINED arg_DIRECTORY)
    set(arg_DIRECTORY ${PROJECT_ROOT_DIR_iUj6dGn1gNrOcYQ7}/${arg_DIRECTORY})
  endif()
  if(DEFINED arg_SOURCES)
    list(TRANSFORM arg_SOURCES PREPEND ${arg_DIRECTORY}/)
  endif()
  if(DEFINED arg_PRIVATE_HEADERS)
    list(TRANSFORM arg_PRIVATE_HEADERS PREPEND ${arg_DIRECTORY}/internal/)
  endif()
  if(DEFINED arg_PUBLIC_HEADERS)
    if(NOT DEFINED arg_INCLUDE_PREFIX)
      set(arg_INCLUDE_PREFIX ${arg_TARGET})
    endif()
    list(TRANSFORM arg_PUBLIC_HEADERS
         PREPEND ${arg_DIRECTORY}/include/${arg_INCLUDE_PREFIX}/)
  endif()
endmacro()

macro(prepare_platform_specific_paths)
  if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(operating_system_name "linux")
  endif()

  set(PROJECT_ROOT_DIR_wzKU1TwtQcyRd9pA ${CMAKE_CURRENT_SOURCE_DIR}/..)

  if(DEFINED arg_DIRECTORY)
    set(arg_DIRECTORY ${PROJECT_ROOT_DIR_wzKU1TwtQcyRd9pA}/${arg_DIRECTORY})
  endif()
  if(DEFINED arg_SOURCES)
    list(TRANSFORM arg_SOURCES
         PREPEND ${arg_DIRECTORY}/${operating_system_name}/)
  endif()
  if(DEFINED arg_PRIVATE_HEADERS)
    list(TRANSFORM arg_PRIVATE_HEADERS PREPEND ${arg_DIRECTORY}/internal/)
  endif()
  if(DEFINED arg_PUBLIC_HEADERS)
    list(TRANSFORM arg_PUBLIC_HEADERS
         PREPEND ${arg_DIRECTORY}/include/${arg_TARGET}/)
  endif()
endmacro()

macro(common_macros)
  links_and_sources()
  conditionally_enable_coverage()
  conditionally_enable_address_sanitizer()
  conditionally_enable_undefined_behaviour_sanitizer()
  standard_presets()
endmacro()

macro(common_test_macros)
  exclude_from_all()
  add_to_all_tests()
  define_tests()
  disable_exceptions_in_coverage_mode()
endmacro()

function(new_implementation_library)
  set(options PLACEHOLDER_OPTION)
  set(singleValueKeywords DIRECTORY TARGET INCLUDE_PREFIX)
  set(multiValueKeywords PRIVATE_LINKS PUBLIC_LINKS PRIVATE_HEADERS
                         PUBLIC_HEADERS SOURCES)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  prepare_paths()

  add_library(${arg_TARGET})
  target_compile_features(
    ${arg_TARGET}
    PRIVATE cxx_std_23
    PUBLIC cxx_std_11)

  install_public_headers()
  disable_exceptions_in_coverage_mode()
  conditionally_enable_pic()
  common_macros()
endfunction()

function(new_exported_library)
  set(options PLACEHOLDER_OPTION)
  set(singleValueKeywords TARGET)
  set(multiValueKeywords INTERFACE_LINKS)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  prepare_paths()

  add_library(${arg_TARGET} INTERFACE)
  target_compile_features(${arg_TARGET} INTERFACE cxx_std_11)

  interface_links()
endfunction()

function(new_internal_library)
  set(options PLACEHOLDER_OPTION)
  set(singleValueKeywords DIRECTORY TARGET)
  set(multiValueKeywords PRIVATE_LINKS PRIVATE_HEADERS PUBLIC_HEADERS SOURCES)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  prepare_paths()

  add_library(${arg_TARGET} STATIC)
  target_compile_features(
    ${arg_TARGET}
    PRIVATE cxx_std_23
    PUBLIC cxx_std_23)

  do_not_install_public_headers()
  disable_exceptions_in_coverage_mode()
  conditionally_enable_pic()
  common_macros()
endfunction()

function(new_platform_specific_internal_library)
  set(options PLACEHOLDER_OPTION)
  set(singleValueKeywords DIRECTORY TARGET)
  set(multiValueKeywords PRIVATE_LINKS PRIVATE_HEADERS PUBLIC_HEADERS SOURCES)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  prepare_platform_specific_paths()

  add_library(${arg_TARGET} STATIC)
  target_compile_features(
    ${arg_TARGET}
    PRIVATE cxx_std_23
    PUBLIC cxx_std_23)

  do_not_install_public_headers()
  disable_exceptions_in_coverage_mode()
  conditionally_enable_pic()
  common_macros()
endfunction()

function(new_test_library)
  set(options PLACEHOLDER_OPTION)
  set(singleValueKeywords DIRECTORY TARGET)
  set(multiValueKeywords PRIVATE_LINKS PRIVATE_HEADERS PUBLIC_HEADERS SOURCES)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  prepare_paths()

  add_library(${arg_TARGET} STATIC)
  target_compile_features(
    ${arg_TARGET}
    PRIVATE cxx_std_23
    PUBLIC cxx_std_23)

  do_not_install_public_headers()
  exclude_from_all()
  common_macros()
endfunction()

function(new_basic_test name)
  set(arg_TARGET ${name})
  set(arg_DIRECTORY test/functional_tests/${name})
  set(arg_SOURCES main.cpp)
  set(arg_PRIVATE_LINKS waypoint test_helpers)

  prepare_paths()

  add_executable(${arg_TARGET})
  target_compile_features(${arg_TARGET} PRIVATE cxx_std_23)

  common_test_macros()
  common_macros()
endfunction()

function(new_waypoint_main_test)
  set(options EXPECTED_FAILURE)
  set(singleValueKeywords TARGET)
  set(multiValueKeywords PLACEHOLDER_MULTI_VALUE)
  cmake_parse_arguments(PARSE_ARGV 0 "arg" "${options}"
                        "${singleValueKeywords}" "${multiValueKeywords}")

  set(arg_DIRECTORY test/functional_tests/${arg_TARGET})
  set(arg_SOURCES main.cpp)
  set(arg_PRIVATE_LINKS waypoint_main test_helpers)

  prepare_paths()

  add_executable(${arg_TARGET})
  target_compile_features(${arg_TARGET} PRIVATE cxx_std_23)

  common_test_macros()
  common_macros()
endfunction()

function(new_impl_test name)
  set(arg_TARGET ${name})
  set(arg_DIRECTORY test/functional_tests/${name})
  set(arg_SOURCES main.cpp)
  set(arg_PRIVATE_LINKS waypoint test_helpers)

  prepare_paths()

  set(PROJECT_ROOT_DIR_s2GsE9Ma9zBssF2X ${CMAKE_CURRENT_SOURCE_DIR}/..)

  add_executable(${arg_TARGET})
  target_compile_features(${arg_TARGET} PRIVATE cxx_std_23)
  target_link_libraries(${name} PRIVATE assert coverage process)
  target_include_directories(
    ${name}
    PRIVATE ${PROJECT_ROOT_DIR_s2GsE9Ma9zBssF2X}/src/waypoint/internal
            ${PROJECT_ROOT_DIR_s2GsE9Ma9zBssF2X}/src/waypoint/include/waypoint)

  common_test_macros()
  common_macros()
endfunction()

function(new_cxx_std_11_test name)
  set(arg_TARGET ${name})
  set(arg_DIRECTORY test/functional_tests/${name})
  set(arg_SOURCES main.cpp)
  set(arg_PRIVATE_LINKS waypoint)

  prepare_paths()

  add_executable(${arg_TARGET})
  target_compile_features(${arg_TARGET} PRIVATE cxx_std_11)

  common_test_macros()
  common_macros()
endfunction()

function(new_multifile_test name)
  set(arg_TARGET ${name})
  set(arg_DIRECTORY test/functional_tests/${name})
  set(arg_SOURCES main.cpp test0.cpp test1.cpp test2.cpp test3.cpp)
  set(arg_PRIVATE_LINKS waypoint)

  prepare_paths()

  add_executable(${arg_TARGET})
  target_compile_features(${arg_TARGET} PRIVATE cxx_std_23)

  common_test_macros()
  common_macros()
endfunction()

function(prepare_installation)
  add_library(waypoint::waypoint ALIAS waypoint)
  add_library(waypoint::waypoint_main ALIAS waypoint_main)

  if(BUILD_SHARED_LIBS)
    install(
      TARGETS waypoint waypoint_impl waypoint_main waypoint_main_impl
              library_interface_headers_waypoint_impl
      EXPORT waypoint-targets
      FILE_SET interface_headers_waypoint_impl
      ARCHIVE DESTINATION lib/$<CONFIG>
      LIBRARY DESTINATION lib/$<CONFIG>
      RUNTIME DESTINATION bin/$<CONFIG>)
  else()
    install(
      TARGETS waypoint
              waypoint_impl
              waypoint_main
              waypoint_main_impl
              assert
              coverage
              process
              library_interface_headers_waypoint_impl
      EXPORT waypoint-targets
      FILE_SET interface_headers_waypoint_impl
      ARCHIVE DESTINATION lib/$<CONFIG>
      LIBRARY DESTINATION lib/$<CONFIG>
      RUNTIME DESTINATION bin/$<CONFIG>)
  endif()
  install(
    EXPORT waypoint-targets
    DESTINATION cmake
    FILE waypoint-config.cmake
    NAMESPACE waypoint::)

  include(CMakePackageConfigHelpers)
  write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/waypoint-config-version.cmake
    COMPATIBILITY ExactVersion)

  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/waypoint-config-version.cmake
          DESTINATION cmake)
endfunction()
