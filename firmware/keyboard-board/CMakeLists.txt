# Terminal 1 keyboard and power board firmware (RP2040, Raspberry Pi Pico SDK + TinyUSB).
#
#   keyboard board:  cmake -S firmware/keyboard-board -B build/keyboard-board -DPICO_SDK_PATH=/path/to/pico-sdk
#   bench (a Pico):  cmake -S firmware/keyboard-board -B build/bench -DPICO_SDK_PATH=/path/to/pico-sdk -DTERMINAL_BOARD=bench
#   then:            cmake --build build/keyboard-board     -> terminal-keyboard-board-firmware.uf2
#
# The firmware version is set here, in project(), and nowhere else (semantic versioning; see README.md).
# Host-side unit tests are a separate CMake project in test/ (they build with the computer's own compiler).
cmake_minimum_required(VERSION 3.13)

set(TERMINAL_BOARD "keyboard-board" CACHE STRING "Target: keyboard-board (the Terminal 1 board) or bench (a plain Raspberry Pi Pico)")
set_property(CACHE TERMINAL_BOARD PROPERTY STRINGS keyboard-board bench)
if(NOT TERMINAL_BOARD STREQUAL "keyboard-board" AND NOT TERMINAL_BOARD STREQUAL "bench")
    message(FATAL_ERROR "TERMINAL_BOARD must be keyboard-board or bench, not '${TERMINAL_BOARD}'")
endif()

set(PICO_BOARD pico CACHE STRING "Pico SDK board (the keyboard board uses the same flash and crystal as a Pico)")

include(${CMAKE_CURRENT_LIST_DIR}/pico_sdk_import.cmake)

project(terminal_keyboard_firmware VERSION 0.1.0 LANGUAGES C CXX ASM)
set(CMAKE_C_STANDARD 11)

pico_sdk_init()

set(FIRMWARE_NAME terminal-${TERMINAL_BOARD}-firmware)
if(TERMINAL_BOARD STREQUAL "bench")
    set(BENCH 1)
else()
    set(BENCH 0)
endif()

add_executable(${FIRMWARE_NAME}
    src/main.c
    src/backlight.c
    src/bq25895.c
    src/debounce.c
    src/hid_report.c
    src/i2c_bus.c
    src/keyboard_matrix.c
    src/keymap.c
    src/keymap_table.c
    src/max17048.c
    src/power_state.c
    src/status_protocol.c
    src/sticky_modifiers.c
    src/trackpad.c
    src/trackpad_logic.c
    src/usb_descriptors.c)

target_include_directories(${FIRMWARE_NAME} PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src)
target_compile_definitions(${FIRMWARE_NAME} PRIVATE
    FIRMWARE_VERSION="${PROJECT_VERSION}"
    TERMINAL_BOARD_BENCH=${BENCH})
target_compile_options(${FIRMWARE_NAME} PRIVATE -Wall -Wextra)
target_link_libraries(${FIRMWARE_NAME}
    pico_stdlib
    pico_unique_id
    hardware_i2c
    hardware_pwm
    hardware_watchdog
    tinyusb_device
    tinyusb_board)

pico_set_program_name(${FIRMWARE_NAME} "Terminal 1 keyboard firmware (${TERMINAL_BOARD})")
pico_set_program_version(${FIRMWARE_NAME} "${PROJECT_VERSION}")
pico_add_extra_outputs(${FIRMWARE_NAME})
