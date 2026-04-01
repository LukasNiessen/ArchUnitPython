"""Verify project setup is correct."""


def test_import():
    import archunitpy

    assert archunitpy.__version__ == "0.1.0"
