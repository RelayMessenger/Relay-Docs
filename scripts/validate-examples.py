#!/usr/bin/env python3
import json
import re
import subprocess
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
json_count = 0
bash_count = 0

for path in sorted(root.rglob("*.mdx")):
    if "node_modules" in path.parts:
        continue

    language = None
    block = []
    block_number = 0

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if language is None:
            opening = re.match(r"^```(json|bash)(?:\s.*)?$", stripped)
            if opening:
                language = opening.group(1)
                block = []
            continue

        if stripped != "```":
            block.append(line.strip() if line.startswith("    ") else line)
            continue

        block_number += 1
        source = "\n".join(block) + "\n"

        if language == "json":
            try:
                json.loads(source)
            except json.JSONDecodeError as error:
                raise SystemExit(
                    f"{path.relative_to(root)}: JSON block "
                    f"{block_number}: {error}"
                ) from error
            json_count += 1
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".sh") as file:
                file.write(source)
                file.flush()
                result = subprocess.run(
                    ["bash", "-n", file.name],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if result.returncode:
                raise SystemExit(
                    f"{path.relative_to(root)}: bash block "
                    f"{block_number}: {result.stderr}"
                )
            bash_count += 1

        language = None
        block = []

    if language is not None:
        raise SystemExit(
            f"{path.relative_to(root)}: unclosed {language} block"
        )

print(
    f"validated {json_count} JSON examples and "
    f"{bash_count} bash/cURL examples"
)
