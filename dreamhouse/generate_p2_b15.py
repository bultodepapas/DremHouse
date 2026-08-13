"""Generate the D-059 refined double-frame P2 exterior-envelope revision."""

from __future__ import annotations

import json
from pathlib import Path

from dreamhouse.generate_p2_b09 import generate, load_model

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("p2_b15.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b15_p2"


def main() -> None:
    model = load_model(DATA)
    report = generate(
        model,
        OUT,
        source_path=DATA,
        generator_name="dreamhouse/generate_p2_b15.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()
