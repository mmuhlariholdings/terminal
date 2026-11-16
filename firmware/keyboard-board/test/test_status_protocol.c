/* test_status_protocol.c: host tests for the CDC status line protocol (src/status_protocol.c). */
#include <string.h>

#include "status_protocol.h"
#include "test_framework.h"
#include "trackpad_logic.h"

static struct status_command feed_line(struct status_line_reader *reader, const char *text)
{
    char line[STATUS_LINE_MAX];
    struct status_command command = {STATUS_COMMAND_NONE, 0, NULL};
    int lines = 0;
    for (const char *c = text; *c; c++) {
        if (status_reader_feed(reader, *c, line, sizeof(line))) {
            command = status_parse_line(line);
            lines++;
        }
    }
    CHECK_EQUAL(1, lines);
    return command;
}

int main(void)
{
    char out[STATUS_LINE_MAX];

    /* formats, exactly as in system/plan/interfaces.md section 7 */
    status_format_battery(out, sizeof(out), 87, 3987, BATTERY_STATE_DISCHARGING);
    CHECK(strcmp(out, "BAT 87 3987 discharging\n") == 0);
    status_format_battery(out, sizeof(out), 120, -5, BATTERY_STATE_FULL);
    CHECK(strcmp(out, "BAT 100 0 full\n") == 0);
    status_format_battery(out, sizeof(out), 0, 0, BATTERY_STATE_NO_BATTERY);
    CHECK(strcmp(out, "BAT 0 0 no-battery\n") == 0);
    status_format_power_event(out, sizeof(out), "button-long");
    CHECK(strcmp(out, "PWR button-long\n") == 0);
    status_format_version(out, sizeof(out), "0.1.0", "A");
    CHECK(strcmp(out, "VER 0.1.0 A\n") == 0);
    CHECK_EQUAL(0, status_format_version(out, 4, "0.1.0", "A")); /* does not fit */

    /* battery state from the charger status */
    CHECK_EQUAL(BATTERY_STATE_NO_BATTERY, status_battery_state(false, true, 2));
    CHECK_EQUAL(BATTERY_STATE_DISCHARGING, status_battery_state(true, false, 2));
    CHECK_EQUAL(BATTERY_STATE_CHARGING, status_battery_state(true, true, 1));
    CHECK_EQUAL(BATTERY_STATE_CHARGING, status_battery_state(true, true, 2));
    CHECK_EQUAL(BATTERY_STATE_FULL, status_battery_state(true, true, 3));
    CHECK(strcmp(status_battery_state_name(BATTERY_STATE_CHARGING), "charging") == 0);

    /* commands */
    struct status_line_reader reader;
    status_reader_init(&reader);
    struct status_command command = feed_line(&reader, "VER\n");
    CHECK_EQUAL(STATUS_COMMAND_VERSION, command.kind);
    CHECK(status_reply(&command, out, sizeof(out), "0.1.0", "A") > 0);
    CHECK(strcmp(out, "VER 0.1.0 A\n") == 0);

    command = feed_line(&reader, "PING\r\n");
    CHECK_EQUAL(STATUS_COMMAND_PING, command.kind);
    status_reply(&command, out, sizeof(out), "0.1.0", "A");
    CHECK(strcmp(out, "OK\n") == 0);

    command = feed_line(&reader, "BL 40\n");
    CHECK_EQUAL(STATUS_COMMAND_BACKLIGHT, command.kind);
    CHECK_EQUAL(40, command.value);
    command = feed_line(&reader, "BL 101\n");
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);
    status_reply(&command, out, sizeof(out), "0.1.0", "A");
    CHECK(strncmp(out, "ERR ", 4) == 0);
    command = feed_line(&reader, "BL x\n");
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);
    command = feed_line(&reader, "BL \n");
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);

    command = feed_line(&reader, "MODE mouse\n");
    CHECK_EQUAL(STATUS_COMMAND_MODE, command.kind);
    CHECK_EQUAL(TRACKPAD_MODE_MOUSE, command.value);
    command = feed_line(&reader, "MODE arrows\n");
    CHECK_EQUAL(TRACKPAD_MODE_ARROWS, command.value);
    command = feed_line(&reader, "MODE sideways\n");
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);

    command = feed_line(&reader, "HELLO\n");
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);
    status_reply(&command, out, sizeof(out), "0.1.0", "A");
    CHECK(strcmp(out, "ERR unknown command\n") == 0);

    command = feed_line(&reader, "\n");
    CHECK_EQUAL(STATUS_COMMAND_NONE, command.kind);
    CHECK_EQUAL(0, status_reply(&command, out, sizeof(out), "0.1.0", "A"));

    /* an over-long line is rejected as a whole, and the next line works */
    char longline[200];
    memset(longline, 'X', sizeof(longline) - 2);
    longline[sizeof(longline) - 2] = '\n';
    longline[sizeof(longline) - 1] = '\0';
    command = feed_line(&reader, longline);
    CHECK_EQUAL(STATUS_COMMAND_INVALID, command.kind);
    command = feed_line(&reader, "PING\n");
    CHECK_EQUAL(STATUS_COMMAND_PING, command.kind);

    return test_summary("status_protocol");
}
