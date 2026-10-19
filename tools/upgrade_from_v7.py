#!/usr/bin/env python3
"""Upgrade an ALREADY PATCHED audio-only v7 CH552 checkout to v8 packed PDM.

For a clean upstream checkout, use install_into_upstream.py instead.
"""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
FILES = ['audio.c', 'audio.h', 'audio_settings.h', 'tick.c', 'main.c']


def upgrade(repo: Path):
    a = repo / 'src/audio.c'
    if not a.exists():
        raise ValueError('No src/audio.c found: use install_into_upstream.py for a clean upstream checkout')
    code = a.read_text()
    if 'packed 64-kHz PDM playback' in code:
        raise ValueError('v8 already installed')
    if 'configurable first-order PDM' not in code and '8-kHz PCM' not in code:
        raise ValueError('This does not look like a v7 audio-only checkout. Refusing to overwrite.')
    for name in FILES:
        target = repo / 'src' / name
        bak = repo / '.ch552_audio_v7_backup' / 'src' / name
        bak.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not bak.exists():
            shutil.copy2(target, bak)
        shutil.copy2(ROOT/'src'/name, target)
    (repo / 'host').mkdir(exist_ok=True)
    target=repo/'host/stream_audio.py'
    bak=repo/'.ch552_audio_v7_backup/host/stream_audio.py'
    bak.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not bak.exists(): shutil.copy2(target,bak)
    shutil.copy2(ROOT/'host/stream_audio.py',target)
    print('Updated to v8 packed PDM. Backup in .ch552_audio_v7_backup/')
    print('Rebuild: cd', repo, '&& make clean && make')
    print('WARNING: Use only the v8 streamer with v8 firmware!')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('upstream',type=Path)
    args=p.parse_args()
    try:
        upgrade(args.upstream.resolve())
    except (OSError,ValueError) as e:
        p.exit(2,f'Error: {e}\n')

if __name__=='__main__': main()
