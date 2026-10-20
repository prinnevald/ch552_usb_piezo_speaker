# Third-party notices

This repository is an independent code overlay for
[Tadashi's `tadakado/ch552-dongle`](https://github.com/tadakado/ch552-dongle).
The upstream work is MIT licensed and identifies its copyright holder as:

> Copyright (c) 2026 Tadashi

The upstream USB CDC implementation, USB descriptors, system initialization,
CH552 headers and SDCC build environment are **not copied into this repository**.
Users obtain those files by cloning the upstream project, retaining its LICENSE
and README. The overlay installer patches selected files and adds original audio
playback sources and a host-side audio processor. The upstream LICENSE is never
overwritten by the installer. See this repository's LICENSE for the overlay.

**Not affiliated with or endorsed by Tadashi.** Please cite and link the
original project when redistributing a patched firmware tree.
