"""Offline smoke tests using structurally faithful snippets of the upstream files.
Not a substitute for building with SDCC against a real upstream checkout.
"""
from pathlib import Path
import tempfile
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import install_into_upstream as inst


def test_descriptor_removal():
    sample='''#define CFG_TOTAL_LEN 100
__code const uint8_t cfg_desc[] = {
9, 0x02,
    0x03,                   /* bNumInterfaces = CDC control / CDC data / HID */
    0x00,  /* CDC descriptor bytes here */
    /* --- IF2: HID ------------------------------------------------- */
    9, 0x04,
    IF_HID, 0x00,
    USB_HID_INTERVAL_MS
};
__code const uint8_t str_product[] = {
    24, 0x03,
    'C', 0, 'H', 0
};
'''
    new=inst.descriptors_cdc_only(sample)
    assert '#define CFG_TOTAL_LEN 75' in new
    assert '0x02,/* bNumInterfaces' in new
    assert 'IF_HID, 0x00' not in new
    assert 'CH552 PDM Audio' not in new  # encoded UTF-16LE chars
    assert "'P', 0" in new


def test_install():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)/'ch552-dongle'
        (repo/'src').mkdir(parents=True)
        (repo/'Makefile').write_text('SRCS := $(sort $(wildcard src/*.c))\n')
        (repo/'config.h').write_text('#define FREQ_SYS 24000000UL\n#define USB_PID 0x9002\n')
        (repo/'src'/'usb_desc.c').write_text('''#define CFG_TOTAL_LEN 100
__code const uint8_t cfg_desc[] = {
    0x03,                   /* bNumInterfaces = CDC + HID */
    /* --- IF2: HID ------------------------- */
    9, 0x04,
    USB_HID_INTERVAL_MS
};
__code const uint8_t str_product[] = { 4, 0x03, 'X', 0 };
''')
        (repo/'src'/'usb.c').write_text('''if (setup_iface > IF_HID) return 0;
if (setup_iface > IF_HID) return 0;
''')
        for name in ['main.c', 'sys.c', 'tick.c', 'cdc.c', 'hid.c']:
            (repo/'src'/name).write_text('/* placeholder */\n')
        inst.install(repo)
        assert 'cdc.c main.c sys.c tick.c usb.c usb_desc.c)' in (repo/'Makefile').read_text()
        assert 'hid.c ' not in (repo/'Makefile').read_text()
        assert 'IF2: HID' not in (repo/'src'/'usb_desc.c').read_text()
        assert 'IF_HID' not in (repo/'src'/'usb.c').read_text()
        assert (repo/'src'/'audio.c').is_file()
        assert (repo/'README_AUDIO_OVERLAY.md').is_file()
        assert (repo/'.ch552_audio_backup'/'src'/'usb_desc.c').is_file()


def test_reject_unknown_descriptor_without_changes():
    try:
        inst.descriptors_cdc_only('#define CFG_TOTAL_LEN 95')
    except ValueError: pass
    else: raise AssertionError('should reject altered upstream')

if __name__ == '__main__':
    test_descriptor_removal()
    test_install()
    test_reject_unknown_descriptor_without_changes()
    print('3 overlay smoke tests passed')
