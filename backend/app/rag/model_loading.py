"""Helpers for resolving model sources without slow remote probing."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=16)
def resolve_model_source(model_name: str, local_only: bool) -> str | None:
    path = Path(model_name)
    if path.exists():
        return str(path.resolve())

    if not local_only:
        return model_name

    try:
        from huggingface_hub import snapshot_download

        return snapshot_download(repo_id=model_name, local_files_only=True)
    except Exception:
        return None
