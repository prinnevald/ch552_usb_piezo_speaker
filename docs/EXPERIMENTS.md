# Audio experiments

Current stable hardware-tested baseline: v7, 8 kHz PCM input, 64 kHz first-order PDM. 48 kHz and especially 64 kHz increased intelligibility over 32 kHz. Silence is quiet; audible hiss persists during active music and speech.

v8 experiments (unverified on hardware): move modulator to host computer, stream packed 64 kHz PDM at 8000 USB bytes/s. Compare first and second order at the same switching rate, with the same `bright-wide` audio filter, normalized source clip, and hardware settings. Observe voice intelligibility, hiss level, USB underruns, and whether switching artifacts change.

Longer-term: characterise acoustics by measuring a slow chirp/short tone sweep with a separate microphone. Determine whether buzzer response or electronics dominates, then evaluate an appropriately protected current-limited push-pull/H-bridge driver. Multiple frequency-specialized transducers may require separate safe drivers and additional CH552 outputs; do not parallel 17 ohm coils directly on GPIO.
