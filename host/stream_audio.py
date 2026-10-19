#!/usr/bin/env python3
"""CH552 v8 USB-CDC bit-packed PDM streamer, with host-side noise shaping.

USB protocol: 8000 BYTES/s, each byte has 8 PDM bits (MSB-first), for a
64,000 bits/s GPIO waveform. NOT compatible with older 8-bit PCM firmware.
"""
import argparse
from array import array
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
import wave

PCM_RATE = 8000
PDM_RATE = 64000
UPSAMPLE = PDM_RATE // PCM_RATE

PROFILES = {
    "raw": "anull",
    "bright-wide": (
        "highpass=f=420,lowpass=f=3350,"
        "equalizer=f=1400:t=q:w=0.9:g=5,"
        "equalizer=f=2600:t=q:w=1.0:g=5,"
        "acompressor=threshold=0.12:ratio=3:attack=5:release=75:makeup=2,"
        "alimiter=limit=0.92"
    ),
    "bright": (
        "highpass=f=420,lowpass=f=1820,"
        "equalizer=f=1400:t=q:w=0.9:g=7,"
        "acompressor=threshold=0.12:ratio=3:attack=5:release=75:makeup=2,"
        "alimiter=limit=0.92"
    ),
    "music": (
        "highpass=f=180,lowpass=f=3250,"
        "acompressor=threshold=0.18:ratio=2:attack=10:release=120:makeup=1.6,"
        "alimiter=limit=0.92"
    ),
}


def decode_8k(source: Path, profile: str) -> bytes:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(source),
           "-vn", "-ac", "1", "-af", PROFILES[profile], "-ar", str(PCM_RATE),
           "-acodec", "pcm_u8", "-f", "u8", "-"]
    return subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout


def adjust_gain(samples: bytes, gain: float) -> bytes:
    if gain == 1: return samples
    return bytes(max(0, min(255, round(128 + (sample - 128) * gain))) for sample in samples)


def noise_gate(data: bytes, threshold: float, hold_ms: int) -> bytes:
    if threshold <= 0: return data
    frame = 160  # 20 ms at 8 kHz
    hold_frames = (hold_ms + 19) // 20
    remaining = 0
    output = bytearray(data)
    for start in range(0, len(output), frame):
        chunk = output[start:start + frame]
        rms = math.sqrt(sum((int(s) - 128) ** 2 for s in chunk) / len(chunk))
        if rms >= threshold:
            remaining = hold_frames
        elif remaining > 0:
            remaining -= 1
        else:
            output[start:start + frame] = b"\x80" * len(chunk)
    return bytes(output)


def active_mask(pcm: bytes) -> bytearray:
    """Keep audio active across waveform zero-crossings; mute quiet frames."""
    mask = bytearray(len(pcm))
    frame = 160
    for start in range(0, len(pcm), frame):
        stop = min(start + frame, len(pcm))
        active = any(x != 128 for x in pcm[start:stop])
        if active:
            mask[start:stop] = b"\x01" * (stop - start)
    return mask


def upsample_s16(pcm: bytes) -> array:
    """Band-limited 8-kHz -> 64-kHz interpolation by FFmpeg."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-f", "u8", "-ar", str(PCM_RATE), "-ac", "1", "-i", "pipe:0",
           "-af", "aresample=64000:filter_size=32:phase_shift=10",
           "-acodec", "pcm_s16le", "-f", "s16le", "pipe:1"]
    output = subprocess.run(cmd, input=pcm, stdout=subprocess.PIPE, check=True).stdout
    ints = array("h")
    ints.frombytes(output)
    if sys.byteorder != "little": ints.byteswap()
    # Ensure precisely 8 PDM ticks per original 8 kHz sample. FFmpeg may
    # adjust lengths slightly due to resampling filter delay.
    needed = len(pcm) * UPSAMPLE
    if len(ints) < needed:
        ints.extend([0] * (needed - len(ints)))
    elif len(ints) > needed:
        del ints[needed:]
    return ints


def modulate(pcm: bytes, algorithm: str, amplitude: float = 0.9) -> bytes:
    """Produce 8 bit-packed PDM ticks per PCM sample (MSB-first).

    First order: error-integrating pulse density, same concept as v7.
    Second order: feedback of two integrators; susceptible to idle tones,
    especially near full-scale, so amplitude headroom is intentionally kept.
    """
    if not pcm: return b""
    samples = upsample_s16(pcm)
    mask = active_mask(pcm)
    output = bytearray(len(pcm))
    accumulator = 0.0
    integrator1 = 0.0
    integrator2 = 0.0
    prev_bit = 0.0
    for i, pcm_val in enumerate(pcm):
        if not mask[i]:
            accumulator = integrator1 = integrator2 = prev_bit = 0.0
            continue  # the whole output byte remains zero -> coil off
        packed = 0
        for k in range(UPSAMPLE):
            s16 = samples[i * UPSAMPLE + k]
            density = 0.5 + 0.5 * amplitude * (s16 / 32768.0)
            density = min(0.97, max(0.03, density))
            if algorithm == "first":
                accumulator += density
                bit = 1 if accumulator >= 1.0 else 0
                if bit: accumulator -= 1.0
            else:
                integrator1 += density - prev_bit
                integrator2 += integrator1 - prev_bit
                bit = 1 if integrator2 >= 0.5 else 0
                prev_bit = float(bit)
                # Safety reset if second-order loop becomes numerically unstable.
                # Should not be needed for bounded input with headroom.
                if abs(integrator2) > 1000.0:
                    integrator1 = integrator2 = 0.0
                    prev_bit = 0.0
            packed = (packed << 1) | bit
        output[i] = packed
    return bytes(output)


def save_wav(path: Path, pcm: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(PCM_RATE)
        wav.writeframes(pcm)


def usb_stream(port: str, packed: bytes, chunk: int, prebuffer: int):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Install PySerial: sudo apt install python3-serial") from exc
    prebuffer = min(prebuffer, 160, len(packed))
    prebuffer -= prebuffer % chunk
    with serial.Serial(port, 115200, timeout=0.5, write_timeout=3) as ser:
        time.sleep(0.25)
        if prebuffer: ser.write(packed[:prebuffer])
        sent = prebuffer
        start = time.monotonic()
        while sent < len(packed):
            n = min(chunk, len(packed) - sent)
            deadline = start + (sent - prebuffer + n) / PCM_RATE
            wait = deadline - time.monotonic()
            if wait > 0: time.sleep(wait)
            ser.write(packed[sent:sent+n])
            sent += n
        ser.flush()
    print("USB writes complete. Allow the remaining device buffer to play.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("port", help="/dev/ttyACM0 or preview")
    ap.add_argument("file", type=Path, help="WAV, MP3, etc.")
    ap.add_argument("--profile", choices=PROFILES, default="bright-wide")
    ap.add_argument("--modulator", choices=("first", "second"), default="first")
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--amplitude", type=float, default=0.9, help="PDM amplitude headroom (0.1..0.95)")
    ap.add_argument("--gate", type=float, default=2.5)
    ap.add_argument("--gate-hold", type=int, default=80)
    ap.add_argument("--chunk", type=int, choices=(16, 32, 64), default=32)
    ap.add_argument("--prebuffer", type=int, default=160)
    ap.add_argument("--save-pcm", type=Path, help="save 8 kHz processed audio WAV")
    ap.add_argument("--save-pdm", type=Path, help="save raw 8-bit packed PDM stream")
    args = ap.parse_args()
    if not args.file.is_file(): ap.error("audio file does not exist")
    if not 0.1 <= args.amplitude <= 0.95: ap.error("--amplitude must be 0.1..0.95")
    if not 0.1 <= args.gain <= 3.0: ap.error("--gain must be 0.1..3.0")
    if args.gate < 0 or args.gate_hold < 0 or args.prebuffer < 0: ap.error("gate and prebuffer options must be nonnegative")
    if not shutil.which("ffmpeg"): ap.error("FFmpeg required (sudo apt install ffmpeg)")
    try:
        pcm = decode_8k(args.file, args.profile)
        pcm = noise_gate(adjust_gain(pcm, args.gain), args.gate, args.gate_hold)
        packed = modulate(pcm, args.modulator, args.amplitude)
        print(f"{len(packed)/8000:.2f}s, {len(packed)} USB bytes, 64 kHz packed PDM, "
              f"{args.modulator}-order modulation, profile {args.profile}")
        print(f"Muted frames: {packed.count(0)/max(1,len(packed))*100:.1f}% of bytes (including some active zeros)")
        if args.save_pcm: save_wav(args.save_pcm, pcm)
        if args.save_pdm:
            args.save_pdm.parent.mkdir(parents=True, exist_ok=True)
            args.save_pdm.write_bytes(packed)
        if args.port.lower() != "preview": usb_stream(args.port, packed, args.chunk, args.prebuffer)
        return 0
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
