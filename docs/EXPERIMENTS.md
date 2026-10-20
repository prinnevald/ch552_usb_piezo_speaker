# Listening experiments and baseline

## Stable defaults

- USB CDC transfers 8,000 packed PDM bytes per second.
- The CH552 shifts the packed bits to P3.0 at 64 kHz, timer-driven.
- The Linux host does 8 kHz mono processing and **first-order** PDM.
- `bright-wide` was the preferred EQ profile.
- Tested output stage: BC337 + 1 kΩ base resistor, 100 Ω series to a 17 Ω magnetic buzzer, 1N4007 flyback diode.

## Subjective observations

| Experiment | User observation |
| --- | --- |
| 4 kHz audio, PWM | Speech almost unintelligible, significant noise |
| 4 kHz, 32 kHz PDM | A recognizable hint of speech |
| 8 kHz audio, 32 kHz PDM | Actual words understandable; radio-like |
| 48 and 64 kHz first-order PDM | Both better, 64 kHz especially noticeable |
| 64 kHz host-computed first-order PDM | More comfortable listening |
| 64 kHz host-computed second-order PDM | Louder, higher-pitched, ear-fatiguing tinniness |
| Digital silence | Quiet; hiss only during audio |

The small electromagnetic buzzer was not characterized with calibrated acoustic measurements. Do not interpret perceived loudness as flat frequency response or as proof that noise shaping alone caused an improvement.

## Useful next experiments

1. Measure 100 Hz–4 kHz sweep output with the same microphone, distance and drive level for each configuration; include repeat measurements.
2. Compare first-order PDM and a filtered-PWM approach at matched loudness.
3. Characterize the effect of coil current/diode on transient response, using an oscilloscope and proper inductive-load protection.
4. Move to an RP2040 Pico W with DMA/PIO/hardware PWM to remove MCU ISR overhead; compare using the same transducer before attempting frequency-split outputs.

Do **not** remove the 1N4007 or bridge the coil without a suitably designed driver.
