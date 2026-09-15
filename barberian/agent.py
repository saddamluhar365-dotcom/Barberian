import re

from . import registry


def handle_message(message):
    text = message.strip().lower()

    match = re.fullmatch(r"add\s+(.+?)\s+(mcp|skill)", text)
    if match:
        name, kind = match.groups()
        return registry.add(kind, name)

    match = re.fullmatch(r"(?:list|show)\s+(mcp|skills?)", text)
    if match:
        kind = "skill" if match.group(1).startswith("skill") else "mcp"
        return registry.list_items(kind)

    match = re.fullmatch(r"disable\s+(.+?)\s+(mcp|skill)", text)
    if match:
        name, kind = match.groups()
        return registry.disable(kind, name)

    return {"ok": True, "type": "chat", "message": "Command not recognized yet."}
