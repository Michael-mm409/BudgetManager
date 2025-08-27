from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit

_BULLET_PREFIXES = ("•", "- ", "* ")


def apply_bullets(edit: QTextEdit) -> None:
    lines = edit.toPlainText().splitlines()
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append("")
        elif s.startswith(_BULLET_PREFIXES):
            out.append(s)
        else:
            out.append(f"• {s}")
    edit.setPlainText("\n".join(out))


__all__ = ["apply_bullets"]
