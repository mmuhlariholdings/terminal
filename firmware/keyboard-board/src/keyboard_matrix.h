/*
 * keyboard_matrix.h: scans the Q20 key matrix (7 rows x 6 columns) and the RIGHT2 nav key, plus the power button.
 * Bit n of the result = input n pressed: bits 0-41 matrix (row * 6 + column), bit 42 RIGHT2, bit 43 power button.
 */
#ifndef TERMINAL_KEYBOARD_MATRIX_H
#define TERMINAL_KEYBOARD_MATRIX_H

#include <stdint.h>

#define INPUT_INDEX_POWER_BUTTON 43
#define INPUT_COUNT 44

void keyboard_matrix_init(void);
uint64_t keyboard_matrix_scan(void);

#endif
