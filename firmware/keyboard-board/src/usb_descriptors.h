/* usb_descriptors.h: USB interface numbers and HID report IDs of the composite device (see usb_descriptors.c). */
#ifndef TERMINAL_USB_DESCRIPTORS_H
#define TERMINAL_USB_DESCRIPTORS_H

/* HID instances, in interface order */
enum {
    HID_INSTANCE_KEYBOARD = 0, /* interface 0 */
    HID_INSTANCE_MOUSE = 1,    /* interface 1 */
    HID_INSTANCE_CONTROL = 2,  /* interface 2: consumer + system control */
};

/* report IDs on the control interface */
enum {
    REPORT_ID_CONSUMER = 1,
    REPORT_ID_SYSTEM = 2,
};

/* values of the system control report (TinyUSB TUD_HID_REPORT_DESC_SYSTEM_CONTROL array: 1-based) */
enum {
    SYSTEM_CONTROL_NONE = 0,
    SYSTEM_CONTROL_POWER_DOWN = 1,
};

#define CDC_STATUS_PORT 0 /* interfaces 3 and 4 */

#endif
