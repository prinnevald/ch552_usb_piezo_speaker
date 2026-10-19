#!/usr/bin/env python3
"""Apply this audio-only CH552 overlay to a separately cloned upstream repo.

Upstream code remains in its original repository. This script patches only the
files needed for audio-only USB CDC enumeration and builds, with backups.
It intentionally refuses unknown upstream formats rather than guessing.
"""
import argparse
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("Makefile", "config.h", "src/main.c", "src/sys.c", "src/tick.c",
            "src/usb.c", "src/usb_desc.c", "src/cdc.c", "src/hid.c")
SOURCES = ("main.c", "audio.c", "audio.h", "tick.c", "audio_settings.h")
SOURCE_LIST = "SRCS := $(addprefix src/,audio.c cdc.c main.c sys.c tick.c usb.c usb_desc.c)"


def replace_one(text, pattern, replacement, label, flags=0):
    updated, count = re.subn(pattern, replacement, text, count=0, flags=flags)
    if count != 1:
        raise ValueError(f"Expected exactly one {label} occurrence; found {count}. Upstream changed?")
    return updated


def descriptors_cdc_only(text):
    # Keep upstream HID report symbol in the source for the existing usb.c's
    # legacy control-request implementation; no HID interface is advertised.
    text = replace_one(text, r"(#define\s+CFG_TOTAL_LEN\s+)100\b",
                       r"\g<1>75", "USB configuration length")
    text = replace_one(text,
                       r"(?m)^([ \t]*)0x03,([ \t]*/\*[^\n]*bNumInterfaces[^\n]*\*/)",
                       r"\g<1>0x02,/* bNumInterfaces = CDC control + CDC data */",
                       "USB interface count")
    text = replace_one(text,
                       r"(?ms)^\s*/\* --- IF2: HID[^\n]*\n.*?USB_HID_INTERVAL_MS\s*\n",
                       "", "HID interface descriptor")
    # Rename only the product string, not the author. Keep upstream MIT notice.
    label = "CH552 PDM Audio"
    encoded = ", ".join(f"'{char}', 0" for char in label)
    new_product = ("__code const uint8_t str_product[] = {\n"
                   + f"    {2 + 2 * len(label)}, 0x03,\n    {encoded}\n}};")
    text = replace_one(text,
                       r"__code\s+const\s+uint8_t\s+str_product\[\]\s*=\s*\{.*?\};",
                       new_product, "USB product string", flags=re.S)
    return text


def install(repo):
    if any(not (repo / required).is_file() for required in REQUIRED):
        raise ValueError("Expected an original tadakado/ch552-dongle checkout")
    mk_path, cfg_path = repo / "Makefile", repo / "config.h"
    desc_path, usb_path = repo / "src/usb_desc.c", repo / "src/usb.c"
    mk = mk_path.read_text(encoding="utf-8")
    cfg = cfg_path.read_text(encoding="utf-8")
    desc = desc_path.read_text(encoding="utf-8")
    usb = usb_path.read_text(encoding="utf-8")
    if not re.search(r"#define\s+FREQ_SYS\s+24000000(?:UL|L|U)?\b", cfg):
        raise ValueError("This firmware requires a 24 MHz CH552 at 5 V")

    mk = replace_one(mk, r"(?m)^SRCS\s*:=.*$", SOURCE_LIST, "source-file list")
    cfg = replace_one(cfg, r"(?m)^(#define\s+USB_PID\s+)0x9002\b",
                      r"\g<1>0x9003", "USB PID")
    # Separate PID reduces old composite-descriptor caching by host OS.
    desc = descriptors_cdc_only(desc)
    # Do not report an unsupported (former HID) interface as valid.
    usb, n = re.subn(r"setup_iface > IF_HID", "setup_iface > IF_CDC_DATA", usb)
    if n != 2:
        raise ValueError(f"Expected two interface-range checks in usb.c; found {n}")

    # Full validation above completes before touching the target checkout.
    changes = {mk_path: mk, cfg_path: cfg, desc_path: desc, usb_path: usb}
    for name in SOURCES:
        changes[repo / "src" / name] = (ROOT / "src" / name).read_text(encoding="utf-8")
    backups = repo / ".ch552_audio_backup"
    for target in changes:
        if target.exists():
            bak = backups / target.relative_to(repo)
            bak.parent.mkdir(parents=True, exist_ok=True)
            if not bak.exists():
                shutil.copy2(target, bak)
    for target, content in changes.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (repo / "host").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "host" / "stream_audio.py", repo / "host" / "stream_audio.py")
    shutil.copy2(ROOT / "host" / "requirements.txt", repo / "host" / "requirements.txt")
    shutil.copy2(ROOT / "README.md", repo / "README_AUDIO_OVERLAY.md")
    ignore = repo / ".gitignore"
    old = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if ".ch552_audio_backup/" not in old:
        ignore.write_text(old.rstrip() + "\n\n# Audio-only overlay backups\n.ch552_audio_backup/\n", encoding="utf-8")
    print("Audio-only overlay installed. No button/keyboard firmware is compiled.")
    print("USB descriptors now advertise CDC interfaces only (no HID interface).")
    print("The original upstream LICENSE and README are untouched.")
    print("Run: cd", repo, "&& make clean && make")
    print("Then flash build/fw.bin using the method for your CH552 board.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    try:
        install(args.upstream.resolve())
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")

if __name__ == "__main__":
    main()
