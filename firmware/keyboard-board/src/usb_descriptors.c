/*
 * usb_descriptors.c: USB descriptors of the Terminal 1 keyboard (system/plan/interfaces.md section 7).
 *
 *   interface 0    HID keyboard, boot protocol
 *   interface 1    HID mouse, boot protocol (trackpad in mouse mode)
 *   interface 2    HID consumer control (report 1) + system control (report 2: System Power Down)
 *   interfaces 3-4 CDC ACM "status" serial port: /dev/serial/by-id/usb-Terminal_1_project_Terminal_1_Keyboard_*-if03
 *
 * VID 0x1209 / PID 0x0001 is the pid.codes TEST ID, a placeholder: apply for a free open-hardware PID at
 * https://pid.codes before any device ships, then change USB_PRODUCT_ID here and in interfaces.md.
 */
#include "usb_descriptors.h"

#include <string.h>

#include "pico/unique_id.h"
#include "tusb.h"

#define USB_VENDOR_ID 0x1209
#define USB_PRODUCT_ID 0x0001
#define USB_DEVICE_RELEASE 0x0010 /* BCD: firmware 0.1 */

enum {
    INTERFACE_KEYBOARD = 0,
    INTERFACE_MOUSE,
    INTERFACE_CONTROL,
    INTERFACE_CDC_CONTROL,
    INTERFACE_CDC_DATA,
    INTERFACE_COUNT
};

enum {
    STRING_LANGUAGE = 0,
    STRING_MANUFACTURER,
    STRING_PRODUCT,
    STRING_SERIAL,
    STRING_KEYBOARD,
    STRING_MOUSE,
    STRING_CONTROL,
    STRING_STATUS,
};

#define ENDPOINT_KEYBOARD 0x81
#define ENDPOINT_MOUSE 0x82
#define ENDPOINT_CONTROL 0x83
#define ENDPOINT_CDC_NOTIFY 0x84
#define ENDPOINT_CDC_OUT 0x05
#define ENDPOINT_CDC_IN 0x85

static const tusb_desc_device_t device_descriptor = {
    .bLength = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,
    /* interface association descriptor (CDC) needs the miscellaneous device class */
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor = USB_VENDOR_ID,
    .idProduct = USB_PRODUCT_ID,
    .bcdDevice = USB_DEVICE_RELEASE,
    .iManufacturer = STRING_MANUFACTURER,
    .iProduct = STRING_PRODUCT,
    .iSerialNumber = STRING_SERIAL,
    .bNumConfigurations = 1,
};

uint8_t const *tud_descriptor_device_cb(void)
{
    return (uint8_t const *)&device_descriptor;
}

static const uint8_t keyboard_report_descriptor[] = {TUD_HID_REPORT_DESC_KEYBOARD()};
static const uint8_t mouse_report_descriptor[] = {TUD_HID_REPORT_DESC_MOUSE()};
static const uint8_t control_report_descriptor[] = {
    TUD_HID_REPORT_DESC_CONSUMER(HID_REPORT_ID(REPORT_ID_CONSUMER)),
    TUD_HID_REPORT_DESC_SYSTEM_CONTROL(HID_REPORT_ID(REPORT_ID_SYSTEM)),
};

uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance)
{
    switch (instance) {
    case HID_INSTANCE_KEYBOARD:
        return keyboard_report_descriptor;
    case HID_INSTANCE_MOUSE:
        return mouse_report_descriptor;
    default:
        return control_report_descriptor;
    }
}

#define CONFIGURATION_LENGTH (TUD_CONFIG_DESC_LEN + 3 * TUD_HID_DESC_LEN + TUD_CDC_DESC_LEN)

static const uint8_t configuration_descriptor[] = {
    TUD_CONFIG_DESCRIPTOR(1, INTERFACE_COUNT, 0, CONFIGURATION_LENGTH, TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 100),
    TUD_HID_DESCRIPTOR(INTERFACE_KEYBOARD, STRING_KEYBOARD, HID_ITF_PROTOCOL_KEYBOARD, sizeof(keyboard_report_descriptor),
                       ENDPOINT_KEYBOARD, CFG_TUD_HID_EP_BUFSIZE, 5),
    TUD_HID_DESCRIPTOR(INTERFACE_MOUSE, STRING_MOUSE, HID_ITF_PROTOCOL_MOUSE, sizeof(mouse_report_descriptor),
                       ENDPOINT_MOUSE, CFG_TUD_HID_EP_BUFSIZE, 5),
    TUD_HID_DESCRIPTOR(INTERFACE_CONTROL, STRING_CONTROL, HID_ITF_PROTOCOL_NONE, sizeof(control_report_descriptor),
                       ENDPOINT_CONTROL, CFG_TUD_HID_EP_BUFSIZE, 10),
    TUD_CDC_DESCRIPTOR(INTERFACE_CDC_CONTROL, STRING_STATUS, ENDPOINT_CDC_NOTIFY, 8, ENDPOINT_CDC_OUT, ENDPOINT_CDC_IN, 64),
};

uint8_t const *tud_descriptor_configuration_cb(uint8_t index)
{
    (void)index;
    return configuration_descriptor;
}

static const char *const strings[] = {
    [STRING_MANUFACTURER] = "Terminal 1 project",
    [STRING_PRODUCT] = "Terminal 1 Keyboard",
    [STRING_SERIAL] = NULL, /* the RP2040 flash's unique ID */
    [STRING_KEYBOARD] = "Terminal 1 Keyboard",
    [STRING_MOUSE] = "Terminal 1 Trackpad",
    [STRING_CONTROL] = "Terminal 1 Power Key",
    [STRING_STATUS] = "Terminal 1 Status",
};

static uint16_t string_buffer[33];

uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t language)
{
    (void)language;
    uint8_t length;
    if (index == STRING_LANGUAGE) {
        string_buffer[1] = 0x0409; /* English (United States) */
        length = 1;
    } else {
        char serial[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
        const char *text;
        if (index == STRING_SERIAL) {
            pico_get_unique_board_id_string(serial, sizeof(serial));
            text = serial;
        } else if (index < sizeof(strings) / sizeof(strings[0]) && strings[index]) {
            text = strings[index];
        } else {
            return NULL;
        }
        length = (uint8_t)strlen(text);
        if (length > 32) {
            length = 32;
        }
        for (uint8_t i = 0; i < length; i++) {
            string_buffer[1 + i] = (uint8_t)text[i];
        }
    }
    string_buffer[0] = (uint16_t)((TUSB_DESC_STRING << 8) | (2 * length + 2));
    return string_buffer;
}
