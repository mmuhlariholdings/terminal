/*
 * backlight.c: keyboard backlight PWM. About 1.9 kHz (125 MHz system clock, divider 1, wrap 65535): above flicker, low
 * enough for a slow N-MOSFET. Brightness is squared so the steps look even to the eye.
 */
#include "backlight.h"

#include "board.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"

#define BACKLIGHT_WRAP 65535u

void backlight_init(void)
{
    gpio_set_function(PIN_BACKLIGHT_PWM, GPIO_FUNC_PWM);
    const unsigned slice = pwm_gpio_to_slice_num(PIN_BACKLIGHT_PWM);
    pwm_config config = pwm_get_default_config();
    pwm_config_set_wrap(&config, BACKLIGHT_WRAP);
    pwm_init(slice, &config, true);
    pwm_set_gpio_level(PIN_BACKLIGHT_PWM, 0);
}

void backlight_set_percent(uint8_t percent)
{
    if (percent > 100) {
        percent = 100;
    }
    const uint32_t level = (uint32_t)percent * percent * BACKLIGHT_WRAP / 10000u;
    pwm_set_gpio_level(PIN_BACKLIGHT_PWM, (uint16_t)level);
}
