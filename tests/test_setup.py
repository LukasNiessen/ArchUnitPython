"""Verify project setup is correct."""


def test_import():
    import archunitpython

    assert archunitpython.__version__ == "0.1.0"
