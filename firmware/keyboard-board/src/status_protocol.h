/*
 * status_protocol.h: the CDC "status" line protocol between the keyboard board and Linux (pure logic, unit-tested).
 * The protocol is defined in system/plan/interfaces.md, section 7. ASCII lines ending in "\n" ("\r\n" accepted).
 *
 *   keyboard board -> Linux:  BAT <percent> <millivolts> <state>   PWR <event>   VER <firmware> <board>   OK   ERR <text>
 *   Linux -> keyboard board:  VER   BL <0-100>   MODE arrows|mouse   PING
 */
#ifndef TERMINAL_STATUS_PROTOCOL_H
#define TERMINAL_STATUS_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define STATUS_LINE_MAX 64
#define STATUS_BATTERY_PERIOD_MS 10000

enum battery_state {
    BATTERY_STATE_CHARGING = 0,
    BATTERY_STATE_DISCHARGING,
    BATTERY_STATE_FULL,
    BATTERY_STATE_NO_BATTERY,
};

enum status_command_kind {
    STATUS_COMMAND_NONE = 0, /* empty line: ignore */
    STATUS_COMMAND_VERSION,
    STATUS_COMMAND_BACKLIGHT,
    STATUS_COMMAND_MODE,
    STATUS_COMMAND_PING,
    STATUS_COMMAND_INVALID,
};

struct status_command {
    uint8_t kind;   /* enum status_command_kind */
    int value;      /* BL: 0-100; MODE: enum trackpad_mode */
    const char *error; /* INVALID: text for "ERR <text>" */
};

struct status_line_reader {
    char buffer[STATUS_LINE_MAX];
    size_t length;
    bool overflow;
};

const char *status_battery_state_name(uint8_t state);

/* Charger REG0B CHRG_STAT bits (0 not charging, 1 pre-charge, 2 fast charge, 3 done) -> battery state. */
uint8_t status_battery_state(bool battery_present, bool external_power, uint8_t charge_status);

/* Formatters: write one complete line including "\n"; return its length (0 if it does not fit). */
size_t status_format_battery(char *out, size_t size, int percent, int millivolts, uint8_t state);
size_t status_format_power_event(char *out, size_t size, const char *event);
size_t status_format_version(char *out, size_t size, const char *firmware_version, const char *board_revision);
size_t status_format_ok(char *out, size_t size);
size_t status_format_error(char *out, size_t size, const char *text);

/* Line reader: feed received characters one at a time; returns true when `line` holds a complete line (no newline). */
void status_reader_init(struct status_line_reader *reader);
bool status_reader_feed(struct status_line_reader *reader, char character, char *line, size_t line_size);

struct status_command status_parse_line(const char *line);

/* Build the reply for a command (VER, OK, ERR): returns its length. BL and MODE are applied by the caller. */
size_t status_reply(const struct status_command *command, char *out, size_t size, const char *firmware_version,
                    const char *board_revision);

#endif
