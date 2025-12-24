# Capture Python CLI (Modular)

A Typer-based CLI with pluggable providers for system snapshots.

## Install (dev)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Show commands
capture --help

# List discovered providers
capture list-providers

# Capture only brew (dry-run)
capture capture --dry-run --providers brew --output-dir dev-config-snapshot-TEST

# Capture selected providers
capture capture --include brew,docker --output-dir snapshots

# Verify a snapshot
capture verify snapshots/dev-config-snapshot-YYYYMMDD-HHMMSS

# Restore (preview)
capture restore snapshots/dev-config-snapshot-YYYYMMDD-HHMMSS --dry-run
```

## Providers

- `brew`: Captures Homebrew version, list, config, and dumps a Brewfile.
- More providers will be added (docker, env, git, macos, shell, ssh, vscode, gpg, terraform).

## Authoring Plugins

Third-party providers can register via entry points under `capture.providers`.
Expose a `get_provider()` that returns an object implementing the `Provider` protocol (`name`, `capture(ctx)`, `verify(ctx)`, `restore(ctx)`).

Example `pyproject.toml` entry:

```toml
[project.entry-points."capture.providers"]
myprovider = "my_package.my_module:get_provider"
```
