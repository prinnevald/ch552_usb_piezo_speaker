# ch552_usb_piezo_speaker

**An 8-bit CH552 USB audio experiment:** stream sound from a Linux PC over USB CDC and reproduce it using a tiny passive electromagnetic buzzer and a current-limited transistor driver. The output is deliberately lo-fi, but speech and music are recognizable with the tested configuration.

The project is an **overlay** on [Tadashi's `ch552-dongle`](https://github.com/tadakado/ch552-dongle), not a fork or copy of its full USB stack. To build, clone the upstream project separately, then apply the overlay. The upstream author's MIT license and notices are preserved. See [Attribution](#attribution-and-license).

> **Tested and preferred:** 8 kHz source audio, **64 kHz first-order PDM**, `bright-wide` filtering, no keyboard. A second-order option remains available for experiments, but on the tested buzzer it produced harsher, higher-pitched, ear-fatiguing artifacts. The current code defaults to **first-order**.

## Hardware and playback architecture

```text
PC (WAV/MP3)  ──FFmpeg, 8 kHz mono + bright-wide EQ──┐
                                                      │
             host-side 1st-order PDM at 64 kHz ──────┤
             pack 8 PDM bits per USB byte             │
                                                      ▼
      USB CDC (8000 bytes/s) → CH552 → GPIO P3.0 → BC337 → buzzer
                                             Timer2: 64,000 bits/s
```

- **USB class:** CDC-ACM virtual serial (`/dev/ttyACM*` on Linux), **not** USB Audio Class. The board will **not** appear in the desktop's speaker selection menu. Play files with `host/stream_audio.py`.
- **Input:** decoded 8 kHz mono unsigned PCM on the host. Band-limited resampling provides eight PDM decisions per audio sample.
- **On-wire format:** one byte contains eight PDM output bits, **most significant bit first**. Stream rate is approximately **8 kB/s**; GPIO bit rate is **64 kHz**.
- **Output:** unipolar transistor switch with noise-gated silence; no Z/X switches or HID keyboard interface.
- **Not a piezo disc:** The tested transducer is a **17 Ω electromagnetic passive buzzer**. The repository name reflects how the experiment began, not its transducer construction.

### Wiring used for listening tests

| Component | Connection |
| --- | --- |
| CH552 **P3.0** | **1 kΩ** resistor → BC337 **base** |
| BC337 **emitter** | GND, common with CH552 |
| BC337 **collector** | Buzzer negative terminal |
| Buzzer positive terminal | **100 Ω** series resistor → +5 V |
| **1N4007** flyback diode | Across the buzzer: **striped cathode to buzzer positive**, anode to collector |

```text
          +5 V
            │
         [100 Ω]
            │───────────────┐
            │               │ cathode (stripe)
        buzzer (+)          |<|  1N4007
        buzzer (−)          │ anode
            │───────────────┘
            │
            C       BC337 (NPN)
P3.0─[1kΩ]─B
            E
            │
           GND  (common with CH552)
```

**Electrical precautions:** Confirm the BC337 pin order for *your* package. Never connect this low-resistance magnetic buzzer directly to GPIO. Keep the diode across the coil (striped end toward positive) and the series resistor. Use a resistor rated **at least ¼ W**, and check for heat during longer playback. A 100 Ω series resistor gives roughly 40 mA worst-case steady-state collector current at 5 V; real coil current depends on its inductance. The CH552 in this setup runs at 5 V / 24 MHz.

## Install (Debian/Ubuntu)

### 1. Dependencies

```bash
sudo apt update
sudo apt install git make sdcc ffmpeg python3 python3-serial
```

Install a compatible CH55x flashing utility separately (for example `ch55xtool`) or reuse your known working CH552 flash method.

### 2. Clone the upstream firmware and this overlay

From the same parent folder:

```bash
git clone https://github.com/tadakado/ch552-dongle.git
git clone https://github.com/YOUR_USERNAME/ch552_usb_piezo_speaker.git
```

Replace `YOUR_USERNAME` with the owner of your published repository. If you downloaded the project as a ZIP, extract the **`ch552_usb_piezo_speaker/`** folder alongside **`ch552-dongle/`** instead.

### 3. Patch, build, and flash

```bash
python3 ch552_usb_piezo_speaker/tools/install_into_upstream.py ch552-dongle
cd ch552-dongle
make clean && make
```

The installer replaces only the audio-specific firmware sources and patches upstream build/USB descriptors to advertise **CDC only, no HID**. It backs up replaced upstream files in `.ch552_audio_backup/`, **preserves the upstream `README.md` and `LICENSE`**, and creates `README_AUDIO_OVERLAY.md` inside the patched checkout. It requires the expected upstream source layout and a 24 MHz clock definition, and will stop if those do not match.

Inspect the build output: it must fit within CH552 user flash and available xRAM. Enter WCH bootloader mode using your board's normal procedure, then flash the compiled image, e.g.:

```bash
ch55xtool -f build/fw.bin
```

Use this command only if it matches your installed flash utility and bootloader workflow. Unplug/reconnect after flashing.

### 4. Check serial port

```bash
ls -l /dev/ttyACM*
```

Use the port corresponding to the CH552 (often `/dev/ttyACM0`). If you receive a permissions error, your Debian user may need membership in `dialout` (`sudo usermod -aG dialout "$USER"`), followed by logout/login.

## Play sound

After patching, `host/stream_audio.py` is copied into `ch552-dongle/host/`. From the **patched `ch552-dongle/`** folder:

```bash
# Preferred: first-order 64 kHz PDM with bright-wide EQ
python3 host/stream_audio.py /dev/ttyACM0 speech.wav

# Also works with supported compressed formats (FFmpeg is required)
python3 host/stream_audio.py /dev/ttyACM0 music.mp3
```

Defaults: `--modulator first --profile bright-wide`. No flags are required for the listening configuration preferred in testing.

```bash
# A/B comparison: more aggressive shaping (reported harsh on tested buzzer)
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --modulator second

# More headroom if loud material distorts
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --amplitude 0.75

# Less / more aggressive host-level processing
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --profile bright
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --profile raw

# Prepare processed PCM and a packed PDM stream without USB playback
python3 host/stream_audio.py preview speech.wav \
  --save-pcm /tmp/processed.wav --save-pdm /tmp/packed.pdm

# CLI reference
python3 host/stream_audio.py --help
```

`/tmp/processed.wav` is conventional **8 kHz PCM**. `/tmp/packed.pdm` is a **raw packed 64 kHz 1-bit stream**, *not* a playable WAV file.

**Protocol warning:** This streamer requires the current **packed-PDM firmware**. Do not use the old 8 kHz PCM-to-MCU streamer (v6/v7) with this firmware: the USB bytes have a different meaning.

## Measurements and experimental findings

This is an experimental audio output stage—not a high-fidelity loudspeaker. The results below are **subjective listening observations on one transducer**, not calibrated frequency-response measurements.

| Variant | Observation |
| --- | --- |
| 4 kHz samples / basic PWM | Audible activity, speech hard to understand, substantial switching noise |
| 8 kHz PCM / 32 kHz PDM | Words began to become intelligible; still tinny |
| 8 kHz PCM / 48 kHz first-order PDM | Improvement |
| 8 kHz PCM / **64 kHz first-order PDM** | Clearer and more comfortable than lower PDM rates |
| 8 kHz input / 64 kHz **host first-order PDM** | **Current preferred version**, `bright-wide` processing |
| 8 kHz input / 64 kHz host second-order PDM | More pronounced, higher-pitched, uncomfortable tinniness |

**Quiet passages mute properly.** The remaining hiss/distortion occurs predominantly during active speech/music. Possible causes include PDM noise folding, the 17 Ω buzzer's mechanical resonance, transistor/diode nonlinearities, and USB timing artifacts; the precise contribution of each has not been measured.

See [Audio experiments](docs/EXPERIMENTS.md) for the research log and [RP2040 next steps](docs/RP2040_NEXT.md) for a proposed follow-up platform.

## Limitations / troubleshooting

| Symptom | Check |
| --- | --- |
| No `/dev/ttyACM*` | Reconnect, check `dmesg`, distinguish bootloader from application mode |
| Silent after startup | **Expected:** startup tones are disabled |
| No audio | Verify matching packed-PDM firmware, the serial port, P3.0, common ground, transistor orientation, diode direction |
| Very slow or distorted playback | Ensure you're using this repo's streamer, **not** the older raw PCM sender |
| Audio cuts or stutters | Shorten your test file, check USB CDC buffering, host scheduling, and permissions |
| Intelligible but tinny sound | Expected from a small resonant electromagnetic buzzer; compare `bright` / `bright-wide` at matched loudness |
| Sharp whine with second-order | Return to **`--modulator first`** |
| Build fails after upstream update | Restore a known-compatible upstream checkout; installer deliberately rejects unrecognized descriptor layouts |

Use short recordings initially. The host implementation buffers the decoded and modulated file before streaming, rather than functioning as a low-memory live audio device.

## Attribution and license

USB CDC, USB enumeration, system initialization, hardware definitions, and the SDCC build environment are built on **[Tadashi (`tadakado`)'s `ch552-dongle`](https://github.com/tadakado/ch552-dongle)**, **MIT licensed**. Copyright notice: **Copyright (c) 2026 Tadashi**.

This repository **does not redistribute the upstream USB stack**. Its installer modifies a separately cloned upstream checkout. Upstream's `LICENSE` and `README.md` are left intact and the existing notices remain in place. The overlay and host processing code are provided under the included [MIT license](LICENSE). See [Third-party notices](THIRD_PARTY_NOTICES.md). This is an independent experiment, not an official upstream release.

## Next steps

Continue acoustic characterization on the CH552 only if useful; we are moving to an **RP2040 Pico W** for a single-transducer USB audio experiment. Compare the same transducer and source clip at matched loudness; if the improvements are insufficient, consider a **multi-transducer / frequency-band split** with a dedicated driver for each output. See [RP2040_NEXT.md](docs/RP2040_NEXT.md).
