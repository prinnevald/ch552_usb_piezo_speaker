# Third-party notices

This repository is an **overlay** on
[**tadakado/ch552-dongle**](https://github.com/tadakado/ch552-dongle),
a CH552 USB firmware project by **Tadashi** (`tadakado`). Its original
copyright notice is **Copyright (c) 2026 Tadashi** and its license is **MIT**.

The original USB CDC stack, supporting includes, system initialization,
SDCC build system and flashing utilities are **not included** in this overlay.
Users clone the upstream project separately. The overlay replaces/adapts
several files in that checkout, and modifies USB configuration descriptors
and related interface validation to expose CDC without a keyboard.

The bundled LICENSE retains the upstream notice and MIT license text.
An upstream checkout's README and LICENSE are left in place by the installer.
Refer also to the upstream README for acknowledgments of other influences.

This project's original additions are the audio receiving loop, the 8 kHz audio processing pipeline, 64 kHz host-side first- and
second-order PDM bitstream generation, MCU packed-bit output, PC audio
filtering/streaming and English installation documentation. This is **not an official upstream release**.
