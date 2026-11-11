import pytest

pytest.importorskip("PySide6")

from client.desktop.qt.hotkey import parse_hotkey, MODS
from client.desktop.qt.mask import normalize_rects


def test_hotkey_parsing():
    assert parse_hotkey("ctrl+alt+space") == (MODS["ctrl"] | MODS["alt"], 0x20)
    assert parse_hotkey("Ctrl + Shift + K") == (MODS["ctrl"] | MODS["shift"], ord("K"))
    assert parse_hotkey("win+f9") == (MODS["win"], 0x78)
    assert parse_hotkey("alt+1") == (MODS["alt"], ord("1"))


@pytest.mark.parametrize("bad", ["space", "ctrl", "ctrl+alt", "ctrl+a+b", "ctrl+banana", "", "f1"])
def test_hotkey_rejects_dangerous_or_invalid(bad):
    with pytest.raises(ValueError):
        parse_hotkey(bad)                                  # a bare key would steal normal typing


def test_hit_rects_are_clipped_padded_and_untrusted_input_is_ignored():
    out = normalize_rects([[10, 10, 100, 50], [690, 810, 100, 100], [-50, -50, 20, 20], "junk", [1, 2], ["a", 1, 1, 1], [5, 5, 0, 0]], 700, 820, pad=4)
    assert out[0] == (6, 6, 108, 58)
    assert out[1] == (686, 806, 14, 14)                    # clipped to the window
    assert len(out) == 2                                   # fully outside / empty / malformed rects are dropped
    assert normalize_rects("not a list", 700, 820) == [] and len(normalize_rects([[0, 0, 5, 5]] * 500, 700, 820)) == 40
