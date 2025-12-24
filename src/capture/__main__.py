import json
from datetime import datetime
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from .context import Context
from .loader import discover_providers

app = typer.Typer(add_completion=False)
console = Console()


def _default_snapshot_name():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"dev-config-snapshot-{ts}"


@app.callback(invoke_without_command=True)
def main(
    output_dir: Path = typer.Option(Path("."), "--output-dir", "-o", help="Base directory to write snapshots"),
    input_dir: Path = typer.Option(Path("."), "--input-dir", "-i", help="Input snapshot directory for verify/restore/show"),
    include: str = typer.Option("", "--include", help="Comma-separated providers to include"),
    exclude: str = typer.Option("", "--exclude", help="Comma-separated providers to exclude"),
    snapshot_name: str = typer.Option("", "--snapshot-name", help="Override default snapshot name"),
    format: str = typer.Option("json", "--format", help="Output format for metadata"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity"),
    verify: bool = typer.Option(False, "--verify", help="Verify an existing snapshot"),
    restore: bool = typer.Option(False, "--restore", help="Preview restore from an existing snapshot"),
    apply: bool = typer.Option(False, "--apply", help="Actually apply restore changes (without this, only preview)"),
    show: bool = typer.Option(False, "--show", help="Show summary of an existing snapshot"),
    list_providers: bool = typer.Option(False, "--list-providers", help="List discovered providers"),
):
    """Single-command CLI: capture/verify always safe, restore requires --apply to change files."""
    # Safety check: --apply only makes sense with --restore
    if apply and not restore:
        console.print("[yellow]Warning: --apply has no effect without --restore[/yellow]")
    
    include_list = [s for s in include.split(",") if s] or None
    exclude_list = [s for s in exclude.split(",") if s] or None

    providers = discover_providers(include_list, exclude_list)

    if list_providers:
        table = Table(title="Providers")
        table.add_column("Name")
        table.add_column("Module")
        for p in providers:
            table.add_row(p.name, p.__class__.__module__)
        console.print(table)
        raise typer.Exit(code=0)

    if show:
        metadata_path = input_dir / "metadata.json"
        if not metadata_path.exists():
            console.print(f"[red]No metadata found at {metadata_path}[/red]")
            raise typer.Exit(code=1)
        
        meta = json.loads(metadata_path.read_text())
        table = Table(title=f"Snapshot: {input_dir.name}")
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_row("Snapshot Name", meta.get("snapshot_name", "N/A"))
        table.add_row("Created At", meta.get("created_at", "N/A"))
        table.add_row("Providers", ", ".join(meta.get("providers", [])))
        opts = meta.get("options", {})
        table.add_row("Include", str(opts.get("include", "all")))
        table.add_row("Exclude", str(opts.get("exclude", "none")))
        console.print(table)
        
        # Show provider directories
        provider_table = Table(title="Provider Data")
        provider_table.add_column("Provider")
        provider_table.add_column("Status")
        for provider_name in meta.get("providers", []):
            provider_dir = input_dir / provider_name
            if provider_dir.exists():
                provider_table.add_row(provider_name, "[green]✓[/green]")
            else:
                provider_table.add_row(provider_name, "[red]✗[/red]")
        console.print(provider_table)
        
        # Show git analysis if available
        git_analysis_path = input_dir / "git" / "analysis.json"
        if git_analysis_path.exists():
            analysis = json.loads(git_analysis_path.read_text())
            git_table = Table(title="Git: Global Config Candidates")
            git_table.add_column("Config Key", style="yellow")
            git_table.add_column("Value")
            git_table.add_column("Repos", justify="right")
            
            candidates = analysis.get("global_candidates", {})
            # Filter to interesting candidates (not core git internals, used in multiple repos)
            skip_keys = {"core.repositoryformatversion", "core.filemode", "core.bare", 
                        "core.logallrefupdates", "core.ignorecase", "core.precomposeunicode"}
            skip_prefixes = ("remote.", "branch.", "submodule.")
            interesting = {k: v for k, v in candidates.items() 
                          if k not in skip_keys 
                          and not any(k.startswith(p) for p in skip_prefixes)
                          and v["repo_count"] >= 2}
            
            if interesting:
                for key, info in sorted(interesting.items(), key=lambda x: -x[1]["repo_count"]):
                    git_table.add_row(key, info["value"], f"{info['repo_count']}/{info['total_repos']}")
                console.print(git_table)
                console.print(f"[dim]Found {analysis['total_repos']} repos. Promotion commands available in analysis.json[/dim]")
                
                # Show promotion commands if available
                promo_cmds = analysis.get("promotion_commands", [])
                if promo_cmds:
                    console.print("\n[cyan]To promote common settings to global config:[/cyan]")
                    for cmd in promo_cmds[:5]:  # Show first 5
                        console.print(f"  [dim]{cmd}[/dim]")
                    if len(promo_cmds) > 5:
                        console.print(f"  [dim]... and {len(promo_cmds) - 5} more in analysis.json[/dim]")
        
        raise typer.Exit(code=0)

    if verify:
        ctx = Context(
            output_dir=input_dir,
            snapshot_name=input_dir.name,
            include=include_list,
            exclude=exclude_list,
            format=format,
            verbose=verbose,
        )
        table = Table(title="Verification")
        table.add_column("Provider")
        table.add_column("Status")
        for p in providers:
            result = p.verify(ctx)
            table.add_row(p.name, "OK" if result.ok else "FAIL")
        console.print(table)
        raise typer.Exit(code=0)

    if restore:
        if not apply:
            console.print("[cyan]Preview mode (use --apply to actually restore)[/cyan]")
        
        ctx = Context(
            output_dir=input_dir,
            snapshot_name=input_dir.name,
            apply=apply,
            include=include_list,
            exclude=exclude_list,
            format=format,
            verbose=verbose,
        )
        ok_all = True
        for p in providers:
            status = "[yellow]Preview[/yellow]" if not apply else "[bold]Applying[/bold]"
            console.print(f"[cyan]Restoring[/cyan] [bold]{p.name}[/bold] ({status})...")
            result = p.restore(ctx)
            ok_all = ok_all and result.ok
        if ok_all:
            if apply:
                console.print("[green]Restore applied[/green]")
            else:
                console.print("[green]Restore preview complete[/green]")
            raise typer.Exit(code=0)
        else:
            console.print("[red]Restore finished with errors[/red]")
            raise typer.Exit(code=2)

    # Default: capture
    if not providers:
        console.print("[yellow]No providers found[/yellow]")
        raise typer.Exit(code=1)

    name = snapshot_name or _default_snapshot_name()
    snap_dir = output_dir / name
    snap_dir.mkdir(parents=True, exist_ok=True)

    ctx = Context(
        output_dir=snap_dir,
        snapshot_name=name,
        include=include_list,
        exclude=exclude_list,
        format=format,
        verbose=verbose,
    )

    meta = {
        "snapshot_name": name,
        "created_at": datetime.now().isoformat(),
        "options": {
            "include": include_list,
            "exclude": exclude_list,
            "format": format,
            "verbose": verbose,
        },
        "providers": [p.name for p in providers],
    }
    (snap_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

    ok_all = True
    for p in providers:
        console.print(f"[cyan]Capturing[/cyan] [bold]{p.name}[/bold]...")
        result = p.capture(ctx)
        provider_dir = snap_dir / p.name
        provider_dir.mkdir(exist_ok=True)
        (provider_dir / "result.json").write_text(json.dumps(result.details, indent=2))
        ok_all = ok_all and result.ok

    if ok_all:
        console.print(f"[green]Capture complete[/green]: {snap_dir}")
    else:
        console.print(f"[red]Capture finished with errors[/red]: {snap_dir}")
        raise typer.Exit(code=2)
