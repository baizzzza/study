"""Write complete JSON result records with an atomic replacement."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


def write_result(path: Path, record: Mapping[str, object]) -> None:
    contents = json.dumps(dict(record), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(contents + "\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
