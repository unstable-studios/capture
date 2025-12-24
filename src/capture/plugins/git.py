from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import subprocess
import shutil
import json
from collections import defaultdict

from ..provider import Provider, ProviderCaptureResult, ProviderVerifyResult, ProviderRestoreResult
from ..context import Context


@dataclass
class GitProvider(Provider):
    name: str = "git"

    def _find_git_repos(self, search_dirs: List[Path]) -> List[Path]:
        """Find git repositories in common locations."""
        repos = []
        for base_dir in search_dirs:
            if not base_dir.exists():
                continue
            # Search one level deep for git repos
            for item in base_dir.iterdir():
                if item.is_dir():
                    git_dir = item / ".git"
                    if git_dir.exists():
                        repos.append(item)
        return repos

    def _sanitize_repo_name(self, repo_path: Path) -> str:
        """Convert repo path to safe filename."""
        # Replace / with __ and ~ with tilde word
        safe = str(repo_path).replace(str(Path.home()), "~")
        safe = safe.replace("/", "__").replace("~", "~")
        return safe

    def _parse_git_config(self, config_text: str) -> Dict[str, str]:
        """Parse git config output into key-value dict."""
        result = {}
        for line in config_text.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
        return result

    def _generate_promotion_commands(self, global_candidates: Dict[str, Any]) -> List[str]:
        """Generate git config commands to promote repo-local settings to global."""
        commands = []
        # Filter to user-relevant settings (skip git internals)
        skip_keys = {"core.repositoryformatversion", "core.filemode", "core.bare", 
                    "core.logallrefupdates", "core.ignorecase", "core.precomposeunicode"}
        # Also skip remote-specific and branch-specific settings
        skip_prefixes = ("remote.", "branch.", "submodule.")
        
        for key, info in global_candidates.items():
            # Skip internals and repo-specific settings
            if key in skip_keys or any(key.startswith(p) for p in skip_prefixes):
                continue
            if info["repo_count"] >= 2:
                # Only suggest if used in multiple repos
                value = info["value"]
                # Escape quotes in value
                safe_value = value.replace('"', '\\"')
                commands.append(f'git config --global {key} "{safe_value}"')
        
        return commands

    def capture(self, ctx: Context) -> ProviderCaptureResult:
        details: Dict[str, Any] = {}
        provider_dir = ctx.output_dir / self.name
        provider_dir.mkdir(exist_ok=True)
        
        git = shutil.which("git")
        if not git:
            return ProviderCaptureResult(ok=False, details={"error": "git not found"})
        
        ok = True
        
        # Capture version
        try:
            version = subprocess.check_output([git, "--version"], text=True).strip()
            details["version"] = version
            (provider_dir / "version.txt").write_text(version + "\n")
        except subprocess.CalledProcessError as e:
            ok = False
            details["version_error"] = str(e)
        
        # Capture config scopes
        configs = {}
        for scope in ["list", "global", "system"]:
            scope_file = f"config--{scope}.txt"
            args = [git, "config", f"--{scope}", "--list"] if scope != "list" else [git, "config", "--list"]
            try:
                output = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
                configs[scope] = output
                (provider_dir / scope_file).write_text(output)
                details[f"config_{scope}_lines"] = len(output.splitlines())
            except subprocess.CalledProcessError as e:
                details[f"config_{scope}_error"] = str(e)
        
        # Find and capture repo-local configs
        search_dirs = [
            Path.home() / "src",
            Path.home() / "projects",
            Path.home() / "code",
            Path.home() / "dev",
            Path.home() / "workspace",
        ]
        repos = self._find_git_repos(search_dirs)
        
        repo_local_dir = provider_dir / "repo-local"
        repo_local_dir.mkdir(exist_ok=True)
        
        repo_configs = {}
        for repo in repos:
            git_config_file = repo / ".git" / "config"
            if git_config_file.exists():
                safe_name = self._sanitize_repo_name(repo)
                try:
                    # Save raw config file for reference
                    config_content = git_config_file.read_text()
                    (repo_local_dir / f"{safe_name}--gitconfig").write_text(config_content)
                    
                    # Use git config --list --local to get properly formatted keys
                    result = subprocess.run(
                        [git, "-C", str(repo), "config", "--local", "--list"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        repo_configs[str(repo)] = self._parse_git_config(result.stdout)
                except Exception as e:
                    details[f"repo_error_{safe_name}"] = str(e)
        
        details["repos_found"] = len(repos)
        details["repos_captured"] = len(repo_configs)
        
        # Analyze common patterns across repos
        if repo_configs:
            key_counts = defaultdict(lambda: defaultdict(int))
            for repo_path, config in repo_configs.items():
                for key, value in config.items():
                    key_counts[key][value] += 1
            
            # Find settings that appear in multiple repos (candidates for global)
            global_candidates = {}
            for key, value_counts in key_counts.items():
                if len(value_counts) == 1:  # Same value in all repos with this key
                    value, count = list(value_counts.items())[0]
                    if count >= 2:  # Appears in at least 2 repos
                        global_candidates[key] = {
                            "value": value,
                            "repo_count": count,
                            "total_repos": len(repo_configs)
                        }
            
            analysis = {
                "total_repos": len(repo_configs),
                "global_candidates": global_candidates,
                "note": "Keys appearing with same value in 2+ repos could be promoted to global config",
                "promotion_commands": self._generate_promotion_commands(global_candidates)
            }
            (provider_dir / "analysis.json").write_text(json.dumps(analysis, indent=2))
            details["global_candidates"] = len(global_candidates)
        
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
