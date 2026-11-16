# Host-side unit tests for the Terminal 1 keyboard board firmware: the pure logic (key map, sticky modifiers, debounce,
# HID reports, trackpad logic, power state machine, status protocol) built with the computer's own C compiler.
#
#   cmake -S firmware/keyboard-board/test -B build/firmware-tests && cmake --build build/firmware-tests
#   ctest --test-dir build/firmware-tests --output-on-failure
cmake_minimum_required(VERSION 3.13)
project(terminal_keyboard_firmware_tests C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(SOURCE ${CMAKE_CURRENT_LIST_DIR}/../src)

add_library(firmware_logic STATIC
    ${SOURCE}/debounce.c
    ${SOURCE}/sticky_modifiers.c
    ${SOURCE}/keymap.c
    ${SOURCE}/keymap_table.c
    ${SOURCE}/hid_report.c
    ${SOURCE}/trackpad_logic.c
    ${SOURCE}/power_state.c
    ${SOURCE}/status_protocol.c)
target_include_directories(firmware_logic PUBLIC ${SOURCE} ${CMAKE_CURRENT_LIST_DIR})
target_compile_options(firmware_logic PUBLIC -Wall -Wextra -Werror)

enable_testing()
foreach(name debounce keymap power_state status_protocol trackpad_logic)
    add_executable(test_${name} test_${name}.c)
    target_link_libraries(test_${name} firmware_logic)
    add_test(NAME ${name} COMMAND test_${name})
endforeach()
