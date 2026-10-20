# Changelog

## 1.0 — 2026-10

Repository-ready release of the **audio-only CH552** overlay. Uses the
experimentally tested **64 kHz packed host-side first-order PDM**, 8 kHz source
sampling and `bright-wide` as default. No Z/X keyboard interface.

- First-order chosen based on subjective listening; second-order retained for A/B comparison.
- English README with clone/build/flash/use instructions and upstream attribution.
- RP2040 Pico W comparison plan in `docs/RP2040_NEXT.md`.
- Offline smoke tests for the overlay installer and packed host audio.

The included sources are based on the v8 implementation the user tested.
The package has not been independently tested on another CH552 board.
