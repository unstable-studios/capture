import importlib
from importlib.metadata import entry_points
from typing import List, Optional
from .provider import Provider


def discover_providers(include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> List[Provider]:
    providers: List[Provider] = []

    # Built-in providers under capture.plugins
    builtin = ["brew", "git"]
    for mod_name in builtin:
        try:
            mod = importlib.import_module(f"capture.plugins.{mod_name}")
            if hasattr(mod, "get_provider"):
                p = mod.get_provider()
                providers.append(p)
        except Exception:
            continue

    # Entry points for third-party providers
    try:
        eps = entry_points()
        group = eps.select(group="capture.providers")
        for ep in group:
            try:
                p = ep.load()()
                providers.append(p)
            except Exception:
                pass
    except Exception:
        pass

    # Filter by include/exclude
    if include:
        providers = [p for p in providers if p.name in include]
    if exclude:
        providers = [p for p in providers if p.name not in exclude]

    # Deduplicate by name
    seen = set()
    uniq: List[Provider] = []
    for p in providers:
        if p.name not in seen:
            uniq.append(p)
            seen.add(p.name)
    return uniq
