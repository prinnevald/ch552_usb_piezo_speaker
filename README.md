# ch552_usb_piezo_speaker — USB audio laboratory

Audio-only CH552 USB device driving a small **electromagnetic** passive buzzer with pulse-density modulation. Despite the repository's historical name, the tested 17 Ω transducer is **not a piezoelectric speaker**. Uses a 5 V CH552 and a separate current-limited transistor driver.

**v8 experimental mode:** 64 kHz *host-computed, bit-packed PDM*. The host sends eight PDM output bits per USB byte (MSB first), for an 8 kB/s stream. Firmware shifts those bits to P3.0 with Timer2; no keyboard is enumerated. We can compare first-order and second-order sigma-delta modulation without changing firmware. The USB communication still uses the CDC interface, **not USB Audio Class**. This is an experimental follow-up to the successfully tested v7 8 kHz PCM / 64 kHz first-order PDM firmware. **v8 has not yet been tested on hardware.**

## Attribution and licensing

Firmware USB initialization, endpoint handling, and build environment derive from **Tadashi's [ch552-dongle](https://github.com/tadakado/ch552-dongle)**, which is distributed under the MIT license. Our repository intentionally contains only an overlay and host-side audio algorithms. The upstream source and its original `LICENSE`, copyright notice `Copyright (c) 2026 Tadashi`, and `README.md` remain with the separately cloned upstream project. Please see `THIRD_PARTY_NOTICES.md`. The overlay files are MIT licensed; do not replace upstream copyright notices when distributing upstream source.

## Hardware used in the experiment

| CH552 pin | Connection |
| --- | --- |
| **P3.0** | 1 kΩ resistor → BC337 base |
| **GND** | BC337 emitter and common ground |
| **5 V** | 100 Ω series resistor → buzzer positive terminal |
| **Buzzer negative** | BC337 collector |
| **1N4007 flyback diode** | Across buzzer coil: **striped end to buzzer positive**, other end to collector |
| **USB** | PC (built into CH552 board) |

**Check BC337 B/C/E pinout from its datasheet or with a multimeter.** The bare 17 Ω magnetic buzzer must never connect directly to a CH552 GPIO. The series resistor limits coil current. At 5 V, current is approximately 41 mA in the on state; a ≥¼ W 100 Ω resistor is sufficient for this experimental drive. Higher switching rates and higher-duty audio may heat the buzzer and transistor; start with short files and stop if anything warms excessively. Use the driver circuit already verified with v7—no hardware change is needed for v8.

## Requirements (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install git make sdcc ffmpeg python3-serial
```

Install the CH552 flashing utility as required by your board (e.g. `ch55xtool`), and enter bootloader mode before flashing.

## Option A — Upgrade an existing, working v7 audio-only checkout

If your existing `ch552-dongle` folder is *already patched for the audio-only v7 project*, run from the directory containing both folders:

```bash
python3 ch552_usb_piezo_speaker_v8_packed/tools/upgrade_from_v7.py ch552-dongle
cd ch552-dongle
make clean && make
```

The script preserves a copy of your v7 files in `.ch552_audio_v7_backup/`. Then flash `build/fw.bin` exactly as you did for the working v7 setup. **You must flash v8 before using the v8 streamer.** Older PCM and new packed-PDM streams are not compatible.

To revert, restore your v7 files from `.ch552_audio_v7_backup/src/` and `.ch552_audio_v7_backup/host/`, rebuild, and reflash.

## Option B — Fresh upstream checkout

```bash
git clone https://github.com/tadakado/ch552-dongle.git
# Clone this separate overlay repository next to the upstream repo,
# or extract this archive into ch552_usb_piezo_speaker_v8_packed/.
python3 ch552_usb_piezo_speaker_v8_packed/tools/install_into_upstream.py ch552-dongle
cd ch552-dongle
make clean && make
```

The installer removes the original USB HID interface from descriptors and compiles CDC-only audio firmware. It backs up original files to `.ch552_audio_backup/`, retains the upstream license/README, and installs the audio streamer into `host/`.

Once compilation succeeds, flash `build/fw.bin` with your normal CH552 programmer. **Neither the new 64 kHz bit shifter nor the second-order host encoder is hardware-verified yet.** Keep a copy of the v7 working binary.

## Playing sound (after flashing v8)

Confirm which USB serial port was assigned:

```bash
ls /dev/ttyACM*
```

From the `ch552-dongle` folder, test with a short tone or your recorded voice. The default `bright-wide` filter was previously the best-sounding profile for this particular electromagnetic buzzer:

```bash
# 64 kHz PDM, first-order (baseline)
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --modulator first

# Same sound, same switching rate, but second-order sigma-delta
python3 host/stream_audio.py /dev/ttyACM0 speech.wav --modulator second

# Play music
python3 host/stream_audio.py /dev/ttyACM0 song.mp3 --modulator second
```

Test at **matched loudness** using the same 5–10 second clip. Second-order modulation is not guaranteed to sound better with an electromagnetic buzzer; it can generate idle tones or accentuate different artifacts.

Other options:

```bash
# Compare waveform/processing offline, without accessing USB
python3 host/stream_audio.py preview speech.wav --modulator first --save-pdm /tmp/first.pdm --save-pcm /tmp/filtered.wav
python3 host/stream_audio.py preview speech.wav --modulator second --save-pdm /tmp/second.pdm

# Preserve more headroom in heavily compressed tracks
python3 host/stream_audio.py /dev/ttyACM0 song.mp3 --modulator second --amplitude 0.75

# Show all options
python3 host/stream_audio.py --help
```

The `*.pdm` files are **raw packed bitstreams**, not WAV audio and not the old PCM format. For active audio, the output toggles between zero and five volts at P3.0 via the external transistor; for gated silence it holds P3.0 low. A quiet digital input does not imply low coil current unless the host-side noise gate is enabled (default).

### Why this change?

In v7, the CH552 recalculated a first-order PDM decision at every one of 64,000 timer interrupts per second. v8 generates PDM on the PC and only shifts one bit per interrupt. USB data remains **8,000 bytes per second**, and the PCM source is still band-limited to 8 kHz before interpolation to 64 kHz for noise shaping. This design is intended to preserve firmware CPU time while making it easier to compare modulation orders.

## Known limitations and experimental notes

- Audible hiss **during active audio** may come from the coil, transistor nonlinearity, switching current, or unfiltered PDM noise. Silence already mutes successfully in v7. Second-order modulation can move noise rather than eliminate it.
- The 17 Ω magnetic buzzer is resonant near 2 kHz and has poor low-frequency response. Software cannot make it behave like a broadband loudspeaker.
- The 1N4007 flyback diode slows coil-current decay. Don't remove it without redesigning the power stage and protecting the transistor.
- One PDM byte = eight output bits. Use only this v8 streamer with this v8 firmware.
- USB port designation may change after firmware updates; check `/dev/ttyACM*`.
- There are no Z/X buttons, HID keyboard reports, or USB Audio Class descriptors in this audio-only firmware.
- USB streaming timing is host-paced; dropouts are still possible. The 192-byte FIFO offers ~24 ms of buffering at 8 kB/s.

## Suggested experiment

Record one clear 5-second speech clip and one music passage. Compare first-order and second-order modulation at exactly the same host profile (`bright-wide`), source volume, and resistor value. Record clarity, hiss, pitch, and dropouts. Keep the option that is **actually more intelligible**, rather than automatically choosing the mathematically more complicated method.
