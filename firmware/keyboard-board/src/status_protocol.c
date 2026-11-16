/* status_protocol.c: CDC status line protocol (see status_protocol.h and system/plan/interfaces.md section 7). */
#include "status_protocol.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "trackpad_logic.h"

const char *status_battery_state_name(uint8_t state)
{
    switch (state) {
    case BATTERY_STATE_CHARGING:
        return "charging";
    case BATTERY_STATE_DISCHARGING:
        return "discharging";
    case BATTERY_STATE_FULL:
        return "full";
    default:
        return "no-battery";
    }
}

uint8_t status_battery_state(bool battery_present, bool external_power, uint8_t charge_status)
{
    if (!battery_present) {
        return BATTERY_STATE_NO_BATTERY;
    }
    if (!external_power) {
        return BATTERY_STATE_DISCHARGING;
    }
    switch (charge_status & 3u) {
    case 1: /* pre-charge */
    case 2: /* fast charge */
        return BATTERY_STATE_CHARGING;
    case 3: /* charge termination done */
        return BATTERY_STATE_FULL;
    default:
        /* USB power present but not charging (fault, temperature, or charging disabled): the cell is not discharging
         * either, so report full only if termination was reached, otherwise discharging is the honest choice */
        return BATTERY_STATE_DISCHARGING;
    }
}

static size_t finish(int written, size_t size)
{
    return (written > 0 && (size_t)written < size) ? (size_t)written : 0;
}

size_t status_format_battery(char *out, size_t size, int percent, int millivolts, uint8_t state)
{
    if (percent < 0) {
        percent = 0;
    }
    if (percent > 100) {
        percent = 100;
    }
    if (millivolts < 0) {
        millivolts = 0;
    }
    return finish(snprintf(out, size, "BAT %d %d %s\n", percent, millivolts, status_battery_state_name(state)), size);
}

size_t status_format_power_event(char *out, size_t size, const char *event)
{
    return finish(snprintf(out, size, "PWR %s\n", event), size);
}

size_t status_format_version(char *out, size_t size, const char *firmware_version, const char *board_revision)
{
    return finish(snprintf(out, size, "VER %s %s\n", firmware_version, board_revision), size);
}

size_t status_format_ok(char *out, size_t size)
{
    return finish(snprintf(out, size, "OK\n"), size);
}

size_t status_format_error(char *out, size_t size, const char *text)
{
    return finish(snprintf(out, size, "ERR %s\n", text), size);
}

void status_reader_init(struct status_line_reader *reader)
{
    memset(reader, 0, sizeof(*reader));
}

bool status_reader_feed(struct status_line_reader *reader, char character, char *line, size_t line_size)
{
    if (character == '\r') {
        return false;
    }
    if (character == '\n') {
        bool complete = !reader->overflow;
        if (complete) {
            size_t length = reader->length < line_size - 1 ? reader->length : line_size - 1;
            memcpy(line, reader->buffer, length);
            line[length] = '\0';
        } else {
            /* too long: report it as an invalid line rather than act on part of it */
            snprintf(line, line_size, "%s", "\x01too-long");
            complete = true;
        }
        reader->length = 0;
        reader->overflow = false;
        return complete;
    }
    if (reader->length < STATUS_LINE_MAX - 1) {
        reader->buffer[reader->length++] = character;
    } else {
        reader->overflow = true;
    }
    return false;
}

static bool parse_percent(const char *text, int *value)
{
    if (*text == '\0') {
        return false;
    }
    char *end = NULL;
    long number = strtol(text, &end, 10);
    if (*end != '\0' || number < 0 || number > 100) {
        return false;
    }
    *value = (int)number;
    return true;
}

struct status_command status_parse_line(const char *line)
{
    struct status_command command = {STATUS_COMMAND_INVALID, 0, "unknown command"};
    while (*line == ' ') {
        line++;
    }
    if (*line == '\0') {
        command.kind = STATUS_COMMAND_NONE;
        command.error = NULL;
        return command;
    }
    if (line[0] == '\x01') {
        command.error = "line too long";
        return command;
    }
    if (strcmp(line, "VER") == 0) {
        command.kind = STATUS_COMMAND_VERSION;
    } else if (strcmp(line, "PING") == 0) {
        command.kind = STATUS_COMMAND_PING;
    } else if (strncmp(line, "BL ", 3) == 0) {
        if (parse_percent(line + 3, &command.value)) {
            command.kind = STATUS_COMMAND_BACKLIGHT;
        } else {
            command.error = "BL needs 0-100";
        }
    } else if (strcmp(line, "MODE arrows") == 0) {
        command.kind = STATUS_COMMAND_MODE;
        command.value = TRACKPAD_MODE_ARROWS;
    } else if (strcmp(line, "MODE mouse") == 0) {
        command.kind = STATUS_COMMAND_MODE;
        command.value = TRACKPAD_MODE_MOUSE;
    } else if (strncmp(line, "MODE", 4) == 0) {
        command.error = "MODE needs arrows or mouse";
    }
    if (command.kind != STATUS_COMMAND_INVALID) {
        command.error = NULL;
    }
    return command;
}

size_t status_reply(const struct status_command *command, char *out, size_t size, const char *firmware_version,
                    const char *board_revision)
{
    switch (command->kind) {
    case STATUS_COMMAND_NONE:
        return 0;
    case STATUS_COMMAND_VERSION:
        return status_format_version(out, size, firmware_version, board_revision);
    case STATUS_COMMAND_INVALID:
        return status_format_error(out, size, command->error ? command->error : "unknown command");
    default:
        return status_format_ok(out, size);
    }
}
