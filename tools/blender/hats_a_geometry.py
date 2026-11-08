"""Kopfbedeckungen Teil A (siehe character_geometry.py)."""
from character_geometry import HATS, make_hats


def build():
    return make_hats(HATS[:4], "HATS_A")
