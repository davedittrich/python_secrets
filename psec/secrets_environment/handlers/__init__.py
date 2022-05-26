# -*- coding: utf-8 -*-

"""
Secrets handlers.
"""

from pathlib import Path


handlers_dir = Path(__file__).parent
# Derive list of supported secret types from files in this directory.
handlers = sorted(
    [
        str(item.stem)
        for item in handlers_dir.iterdir()
        if str(item.stem)[0] not in ['.', '_']
    ]  # noqa
)

__all__ = handlers

# vim: set ts=4 sw=4 tw=0 et :
