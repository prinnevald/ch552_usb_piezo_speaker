/* SPDX-License-Identifier: MIT
 * CH552 USB CDC-only audio receiver (no buttons, HID reports or key scanning).
 * The USB transport and initialization are supplied by tadakado/ch552-dongle.
 * USB input: packed PDM, 8 bits/byte MSB-first, 8000 bytes/second.
 */
#include <stdint.h>
#include "ch552.h"
#include "config.h"
#include "sys.h"
#include "tick.h"
#include "usb.h"
#include "cdc.h"
#include "audio.h"

void main(void)
{
    sys_init();
    tick_init();
    audio_init();
    usb_init();
    EA = 1;
    sys_watchdog_init();

    for (;;) {
        int16_t sample;
        sys_watchdog_feed();

        /* Consume PDM-packed USB CDC bytes only when the FIFO has space.
         * The upstream CDC ring automatically NAKs full bulk OUT packets,
         * so no busy-wait or keyboard-scanning delays are necessary.
         */
        while (audio_has_space()) {
            sample = cdc_getc();
            if (sample < 0) break;
            audio_push((uint8_t)sample);
        }
    }
}
