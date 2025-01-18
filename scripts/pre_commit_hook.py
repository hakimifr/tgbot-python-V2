import os
from pathlib import Path

CONTENT: str = """#!/bin/bash
uv sync  # Make sure dev dependencies are installed
uv run isort .
uv run black .

for file in $(git diff --cached --name-only); do
    test -f "$file" && git add "$file"
done
"""

if Path(".").name == "scripts":
    os.chdir("..")

with open(".git/hooks/pre-commit", "w", encoding="utf-8") as f:
    f.write(CONTENT)
    Path(f.name).chmod(0o755)
