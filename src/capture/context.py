from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class Context:
    output_dir: Path
    snapshot_name: str
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    format: str = "json"
    verbose: int = 0
    # For restore only: if False, shows planned actions without applying
    apply: bool = False
