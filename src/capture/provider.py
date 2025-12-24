from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Protocol, runtime_checkable
from .context import Context

@dataclass
class ProviderCaptureResult:
    ok: bool
    details: Dict[str, Any]

@dataclass
class ProviderVerifyResult:
    ok: bool
    details: Dict[str, Any]

@dataclass
class ProviderRestoreResult:
    ok: bool
    details: Dict[str, Any]

@runtime_checkable
class Provider(Protocol):
    name: str
    def capture(self, ctx: Context) -> ProviderCaptureResult: ...
    def verify(self, ctx: Context) -> ProviderVerifyResult: ...
    def restore(self, ctx: Context) -> ProviderRestoreResult: ...
