/*
 * keyboard_matrix.c: matrix scan, as in the Solder Party i2c_puppet firmware (app/keyboard.c, MIT licence): rows are
 * inputs with pull-ups; each column in turn is driven low and the rows that read low are pressed keys.
 */
#include "keyboard_matrix.h"

#include "board.h"
#include "hardware/gpio.h"
#include "hardware/timer.h"
#include "keymap.h"

static const uint8_t row_pins[KEYBOARD_ROWS] = KEYBOARD_ROW_PINS;
static const uint8_t column_pins[KEYBOARD_COLUMNS] = KEYBOARD_COLUMN_PINS;

static void input_with_pull_up(uint8_t pin)
{
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_IN);
    gpio_pull_up(pin);
}

void keyboard_matrix_init(void)
{
    for (int row = 0; row < KEYBOARD_ROWS; row++) {
        input_with_pull_up(row_pins[row]);
    }
    for (int column = 0; column < KEYBOARD_COLUMNS; column++) {
        input_with_pull_up(column_pins[column]); /* idle columns float high */
    }
    input_with_pull_up(PIN_KEYBOARD_COL7);
    input_with_pull_up(PIN_POWER_BUTTON);
}

uint64_t keyboard_matrix_scan(void)
{
    uint64_t pressed = 0;
    for (int column = 0; column < KEYBOARD_COLUMNS; column++) {
        const uint8_t pin = column_pins[column];
        gpio_put(pin, 0);
        gpio_set_dir(pin, GPIO_OUT);
        busy_wait_us_32(5); /* let the row lines settle */
        const uint32_t levels = gpio_get_all();
        for (int row = 0; row < KEYBOARD_ROWS; row++) {
            if (!(levels & (1u << row_pins[row]))) {
                pressed |= (uint64_t)1 << KEY_INDEX(row, column);
            }
        }
        gpio_set_dir(pin, GPIO_IN);
    }
    const uint32_t levels = gpio_get_all();
    if (!(levels & (1u << PIN_KEYBOARD_COL7))) {
        pressed |= (uint64_t)1 << KEY_INDEX_RIGHT2;
    }
    if (!(levels & (1u << PIN_POWER_BUTTON))) {
        pressed |= (uint64_t)1 << INPUT_INDEX_POWER_BUTTON;
    }
    return pressed;
}
