"""Offline smoke tests for host PDM packing; no CH552 hardware required."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
import stream_audio as audio


def test_packed_silence():
    pcm = bytes([128] * 800)  # 100 ms
    for order in ("first", "second"):
        packed = audio.modulate(pcm, order)
        assert packed == bytes(len(pcm)), f"Non-silent digital silence ({order})"


def test_packed_audio():
    # ~0.1s of nonzero constant signal. 1 byte/sample, 8 bits each.
    pcm = bytes([176] * 800)
    outputs = {}
    for order in ("first", "second"):
        packed = audio.modulate(pcm, order)
        assert len(packed) == len(pcm), (order, len(packed))
        assert any(packed), f"Unexpected entirely zero output ({order})"
        outputs[order] = packed
    assert outputs["first"] != outputs["second"], "Algorithm choice ineffective"


if __name__ == "__main__":
    test_packed_silence()
    test_packed_audio()
    print("2 audio packing smoke tests passed")
