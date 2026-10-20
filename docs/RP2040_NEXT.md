# Next platform: RP2040 Pico W audio evaluation

The next experiment starts with **one transducer**. The existing CH552 build remains the comparison reference, not a requirement for the new Pico W code. No RP2040 firmware is included in this repository.

## Why Pico W?

The RP2040 provides dual 133 MHz Cortex-M0+ cores, 264 KB SRAM, native USB device support, a DMA controller, hardware PWM, and eight PIO state machines. This should allow higher-rate sample generation with much less interrupt overhead than the 24 MHz CH552. Wi-Fi is optional and unrelated to the first USB playback test. Its GPIO is **3.3 V only**, even when the Pico W itself is powered from USB 5 V.

## Proposed staged experiment

1. Select and document the transducer: the existing 17 Ω **electromagnetic** buzzer, a genuine passive **piezoelectric** disc, or both. They need different drive arrangements.
2. Build a properly current-limited, inductive-load-protected driver for the electromagnetic buzzer (don't drive from RP2040 GPIO). A piezo requires different protection; never assume direct GPIO is safe for every transducer.
3. Start with the same audio source, `bright-wide` processing, and 64 kHz first-order PDM as CH552 to establish a fair baseline.
4. Try hardware PWM and PIO/DMA-generated 1-bit streams at higher switching rates. Increase audio bandwidth and experiment with digital filtering, verifying actual output timing and temperature.
5. Measure level versus frequency and compare intelligibility and hiss at matched loudness.
6. Only if a single transducer still sounds poor, consider a **multi-band system**: host splits audio into low/mid/high bands, Pico drives independent outputs, each transducer has its own current-limited amplifier or driver, and their crossover levels are calibrated.

Multiple identical buzzer coils do not automatically create a multi-way speaker. Different acoustic responses and independent output paths are needed. A small conventional dynamic speaker may provide a more revealing control measurement.

## Comparison log template

| System | Transducer | Audio rate | PDM/PWM rate | Processing | Intelligibility | Noise | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CH552 | 17 Ω magnetic buzzer | 8 kHz | 64 kHz PDM | bright-wide, 1st order | baseline | active audio hiss | known working |
| Pico W | TBD | TBD | TBD | same initially | | | |
