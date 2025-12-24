from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass
import subprocess
import shutil

from ..provider import Provider, ProviderCaptureResult, ProviderVerifyResult, ProviderRestoreResult
from ..context import Context


@dataclass
class GitProvider(Provider):
    name: str = "git"

    def capture(self, ctx: Context) -> ProviderCaptureResult:
        details: Dict[str, Any] = {}
        git = shutil.which("git")
        if not git:
            return ProviderCaptureResult(ok=False, details={"error": "git not found"})
        ok = True
        try:
            details["version"] = subprocess.check_output([git, "--version"], text=True).strip()
        except subprocess.CalledProcessError as e:
            ok = False
            details["version_error"] = str(e)
        # Capture configs (best-effort; some may be restricted)
        for scope, args in {
            "list": [git, "config", "--list"],
            "global": [git, "config", "--global", "--list"],
            "system": [git, "config", "--system", "--list"],
        }.items():
            try:
                details[f"config_{scope}"] = subprocess.check_output(args, text=True)
            except subprocess.CalledProcessError as e:
                details[f"config_{scope}_error"] = str(e)
        return ProviderCaptureResult(ok=ok, details=details)

    def verify(self, ctx: Context) -> ProviderVerifyResult:
        git = shutil.which("git")
        ok = git is not None
        return ProviderVerifyResult(ok=ok, details={"git_path": git})

    def restore(self, ctx: Context) -> ProviderRestoreResult:
        # Git provider generally does not auto-restore configs; show plan.
        details: Dict[str, Any] = {}
        details["note"] = "Git configuration restore is manual; review captured configs."
        details["planned"] = [
            "Apply desired git config via 'git config --global key value'",
        ]
        return ProviderRestoreResult(ok=True, details=details)


def get_provider() -> GitProvider:
    return GitProvider()
