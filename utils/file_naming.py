from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable


def safe_filename_stem(filename: str, fallback: str = "report") -> str:
    stem = Path(filename).stem or fallback
    ascii_stem = (
        unicodedata.normalize("NFKD", stem)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_stem)
    safe_stem = safe_stem.strip("._-")
    return safe_stem[:80] or fallback


def unique_folder_names(filenames: Iterable[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique_names: list[str] = []

    for filename in filenames:
        base_name = safe_filename_stem(filename)
        count = seen.get(base_name, 0) + 1
        seen[base_name] = count

        if count == 1:
            unique_names.append(base_name)
        else:
            unique_names.append(f"{base_name}-{count}")

    return unique_names
