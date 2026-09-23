"""Identifiers for the observe stub. Stdlib only — no sandbox.runtime."""

from __future__ import annotations

from uuid import uuid4


def new_id() -> str:
    return uuid4().hex
