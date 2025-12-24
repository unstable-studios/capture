from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass
import subprocess
import shutil

from ..provider import Provider, ProviderCaptureResult, ProviderVerifyResult, ProviderRestoreResult
from ..context import Context


@dataclass
class BrewProvider(Provider):
    name: str = "brew"

    def capture(self, ctx: Context) -> ProviderCaptureResult:
        details: Dict[str, Any] = {}

        brew = shutil.which("brew")
        if not brew:
            return ProviderCaptureResult(ok=False, details={"error": "brew not found"})
        try:
            details["version"] = subprocess.check_output([brew, "--version"], text=True).strip()
            details["list"] = subprocess.check_output([brew, "list"], text=True).splitlines()
            details["config"] = subprocess.check_output([brew, "config"], text=True)
            # Dump Brewfile to provider dir
            provider_dir = ctx.output_dir / self.name
            provider_dir.mkdir(exist_ok=True)
            subprocess.run([brew, "bundle", "dump", "--file", str(provider_dir / "Brewfile"), "--force"], check=True)
            ok = True
        except subprocess.CalledProcessError as e:
            ok = False
            details["error"] = str(e)
        return ProviderCaptureResult(ok=ok, details=details)

    def verify(self, ctx: Context) -> ProviderVerifyResult:
        brew = shutil.which("brew")
        ok = brew is not None
        return ProviderVerifyResult(ok=ok, details={"brew_path": brew})

    def restore(self, ctx: Context) -> ProviderRestoreResult:
        provider_dir = ctx.output_dir / self.name
        brewfile = provider_dir / "Brewfile"
        if not ctx.apply:
            return ProviderRestoreResult(ok=True, details={"planned": f"brew bundle --file {brewfile}"})
        brew = shutil.which("brew")
        if not brew:
            return ProviderRestoreResult(ok=False, details={"error": "brew not found"})
        if not brewfile.exists():
            return ProviderRestoreResult(ok=False, details={"error": "Brewfile missing"})
        try:
            subprocess.run([brew, "bundle", "--file", str(brewfile)], check=True)
            return ProviderRestoreResult(ok=True, details={"applied": str(brewfile)})
        except subprocess.CalledProcessError as e:
            return ProviderRestoreResult(ok=False, details={"error": str(e)})


def get_provider() -> BrewProvider:
    return BrewProvider()
