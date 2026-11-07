#!/usr/bin/env python3
"""Answer the 385-question object worksheet with Claude Haiku, blind to the simulator.

Report: docs/object-properties-v0.md (LLM section). User-approved exception to the
no-bulk-LLM-rows rule (2026-11-07), for this worksheet only. Answers are stored apart
from the hand-written rows and marked as LLM-sourced.

Needs ANTHROPIC_API_KEY in the environment or in the project's git-ignored .env file.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import anthropic

WORKSHEET = Path("data/developmental_graph/relation_authoring/age_6mo_object_properties_worksheet_v0.csv")
OUT = Path("data/developmental_graph/experiments/object_properties_llm_v0")
MODEL = "claude-haiku-5-5"
PROMPT = """Consider a typical {obj} as found in a family home with a 6-month-old baby.
Answer each question from common knowledge. Use "unsure" if it could go either way.

{questions}"""


def load_key() -> None:
    env = Path(".env")
    if os.environ.get("ANTHROPIC_API_KEY") or not env.exists():
        return
    for line in env.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip("'\"")


def main() -> None:
    load_key()
    client = anthropic.Anthropic()
    by_object = defaultdict(list)
    with WORKSHEET.open(newline="") as f:
        for row in csv.DictReader(f):
            by_object[row["object"]].append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    cells, raw, used = [], [], [0, 0]
    for obj, rows in by_object.items():
        fields = [r["field"] for r in rows]
        schema = {"type": "object", "additionalProperties": False, "required": fields,
                  "properties": {f: {"type": "string", "enum": ["yes", "no", "unsure"]} for f in fields}}
        questions = "\n".join(f"{r['field']}: {r['question']}" for r in rows)
        reply = client.messages.create(
            model=MODEL, max_tokens=2000,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": PROMPT.format(obj=obj, questions=questions)}])
        if reply.stop_reason != "end_turn":
            raise SystemExit(f"{obj}: stopped early ({reply.stop_reason})")
        answers = json.loads(next(b.text for b in reply.content if b.type == "text"))
        used[0] += reply.usage.input_tokens
        used[1] += reply.usage.output_tokens
        raw.append({"object": obj, "answers": answers})
        cells += [{"object": obj, "field": f, "value": a == "yes", "sources": [MODEL]}
                  for f, a in answers.items() if a != "unsure"]
        print(obj, answers, flush=True)
    (OUT / "raw_answers.jsonl").write_text("".join(json.dumps(r) + "\n" for r in raw))
    (OUT / "cells.json").write_text(json.dumps({"model": MODEL, "cells": cells}, indent=1))
    cost = used[0] / 1e6 * 0.10 + used[1] / 1e6 * 0.50
    print(f"{len(cells)} cells of {sum(map(len, by_object.values()))}; tokens {used}; about ${cost:.4f}")


if __name__ == "__main__":
    main()
