KNOWN = {
    "mcp": {"github": {"name": "github", "status": "enabled"}},
    "skill": {"research": {"name": "research", "status": "enabled"}},
}

_registry = {"mcp": {}, "skill": {}}


def add(kind, name):
    name = name.strip().lower()
    if name not in KNOWN.get(kind, {}):
        return {"ok": False, "error": f"Unknown {kind}: {name}"}
    _registry[kind][name] = KNOWN[kind][name].copy()
    return {"ok": True, "type": kind, "name": name}


def list_items(kind):
    return {"ok": True, "type": kind, "items": sorted(_registry[kind])}


def disable(kind, name):
    name = name.strip().lower()
    item = _registry[kind].get(name)
    if not item:
        return {"ok": False, "error": f"{kind} not found: {name}"}
    item["status"] = "disabled"
    return {"ok": True, "type": kind, "name": name, "status": "disabled"}
