#!/usr/bin/env python3
"""Create child-language variants for the core5 curriculum.

This is stricter than the controlled-vocabulary pass. It avoids JSON, avoids
schema words, uses colon-delimited fields, and rewrites technical relation
language into simpler first-layer words where possible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any
from output_state import retire_output_dir  # noqa: E402


SPLITS = ("train", "dev", "curriculum_test")
VARIANTS = ("child_plain_text", "child_relation_scaffolded", "child_relation_first_then_text")
WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")
RAW_RE = re.compile(r"\S+")
FIELD_RE_TEMPLATE = r"^{field}:\s*(.*)$"

Example = dict[str, Any]
Record = dict[str, Any]


DOMAIN_WORDS = {
    "agent_6mo_indian_child": "baby world",
    "everyday_physical_world": "thing world",
    "social_world": "people world",
    "math_abstraction": "number world",
    "language_binding": "word world",
}

TASK_WORDS = {
    "counterfactual_contrast": "compare",
    "explanation_path": "why",
    "explanation_with_relations": "why",
    "graph_anchor_from_prompt": "find link",
    "node_id_from_paraphrase": "name thing",
    "relation_completion": "finish link",
    "relation_family_from_prompt": "name kind",
    "state_action_effect": "what happened",
}

NODE_OVERRIDES = {
    "agent.primary_caregiver": "mom dad",
    "agent.other_child": "other child",
    "concept.other_agent_proto": "other person",
    "concept.self_proto": "own body",
    "invariant.comfort_discomfort": "ok not ok",
    "invariant.direct_control": "can move",
    "invariant.expected_unexpected": "known new",
    "invariant.indirect_effect": "can make",
    "invariant.pain_relief": "hurt help",
    "invariant.positive_activation": "happy feel",
    "invariant.connection_gain": "new link",
    "invariant.connection_loss": "lost link",
    "invariant.positive_saturation": "used to it",
    "invariant.direct_valence_shortcut": "fast good feel",
    "invariant.same_different": "same different",
    "object.self_hand": "hand",
    "object.self_mouth": "mouth",
    "schema.happiness_new_connection": "new thing feels good",
    "schema.happiness_existing_connection": "known thing feels good",
    "schema.happiness_saturation": "same good thing gets old",
    "schema.feeding_relief": "milk helps hunger",
    "schema.held_by_caregiver": "held by mom dad",
    "schema.self_motion": "my body moves",
    "schema.word_handle": "word name",
    "schema.relation_cluster_binding": "word means many links",
}

RELATION_WORDS = {
    "absence_can_activate": "missing can wake",
    "action_effect": "does makes",
    "binds_to": "names",
    "built_from": "made from",
    "can_activate": "can wake",
    "can_cause": "can make",
    "can_contact": "can touch",
    "co_occurs_with": "goes with",
    "contrasts_with": "not like",
    "counteracts": "pushes back",
    "directly_controlled_by": "can move",
    "directly_feels": "can feel",
    "enables": "lets",
    "future_built_from": "later made from",
    "has_property": "has",
    "has_relation": "has link",
    "instance_of": "is",
    "modifies": "changes",
    "not_directly_controlled_by": "cannot move",
    "predicts": "tells",
    "selects": "picks",
    "strengthens": "makes strong",
    "strengthens_absence_can_activate": "missing makes strong",
    "strengthens_bind": "names stronger",
    "strengthens_can_activate": "makes wake stronger",
    "strengthens_can_cause": "makes cause stronger",
    "strengthens_co_occurs_with": "goes with stronger",
    "strengthens_contrast": "not like stronger",
    "strengthens_direct_control": "can move stronger",
    "strengthens_has_property": "has stronger",
    "strengthens_instance_of": "is stronger",
    "strengthens_modifies": "changes stronger",
    "strengthens_predicts": "helps know",
    "strengthens_supports": "helps stronger",
    "subject_to": "follows",
    "supports": "helps",
    "updates": "changes",
    "uses": "uses",
}

PHRASE_REPLACEMENTS = (
    ("relation family ids", "kinds"),
    ("relation family", "kind"),
    ("graph anchor ids", "links"),
    ("graph anchors", "links"),
    ("graph anchor", "link"),
    ("answer with relations", "answer with links"),
    ("relation packet", "links"),
    ("relations observed", "links seen"),
    ("relations", "links"),
    ("relation", "link"),
    ("proto self", "own body"),
    ("self proto", "own body"),
    ("self non self", "me not me"),
    ("non self", "not me"),
    ("directly controlled", "can move"),
    ("direct control", "can move"),
    ("not directly controlled", "cannot move"),
    ("sensation", "feel"),
    ("proprioception", "body feel"),
    ("valence", "good bad feel"),
    ("positive activation", "happy feel"),
    ("connection gain", "new link"),
    ("connection loss", "lost link"),
    ("positive saturation", "used to it"),
    ("direct valence shortcut", "fast good feel"),
    ("comfort discomfort", "ok not ok"),
    ("pain relief", "hurt help"),
    ("expected unexpected", "known new"),
    ("supported unsupported", "held not held"),
    ("presence absence", "here gone"),
    ("attention absence", "look not look"),
    ("familiar unfamiliar", "known not known"),
    ("more less equal", "more less same"),
    ("one to one", "one each"),
    ("zero one many", "zero one many"),
    ("same different", "same different"),
    ("inside outside", "in out"),
    ("before after", "before after"),
    ("part whole", "part whole"),
    ("cause effect", "make happen"),
    ("action effect", "do make"),
    ("state change", "change"),
    ("word handle", "word name"),
    ("relation cluster binding", "word means many links"),
    ("contextual relation activation", "place wakes links"),
    ("context selection", "place picks"),
    ("surface meaning separation", "word not thing"),
    ("agent role", "who does"),
    ("quantity relation", "how many"),
    ("property relation", "what kind"),
    ("contextual", "place"),
    ("abstraction", "idea"),
    ("activation", "wake"),
    ("activating", "waking"),
    ("binding", "name"),
    ("cluster", "group"),
    ("classified", "sorted"),
    ("classification", "sorting"),
    ("family", "kind"),
    ("inferred", "guessed"),
    ("interpretation", "meaning"),
    ("membership", "part"),
    ("scaffolded", "with links"),
    ("schema", "way"),
    ("invariant", "rule"),
    ("concept", "thing"),
    ("domain", "world"),
    ("task", "do"),
    ("source", "from"),
    ("target", "to"),
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}: line {line_no} must be a JSON object")
            rows.append(row)
    return rows


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_output_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(f"{path} already exists and is not empty; pass --overwrite")
    if path.exists() and overwrite:
        retire_output_dir(path)
    path.mkdir(parents=True, exist_ok=True)


def simple_text(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("6mo", "six month")
    text = text.replace("->", " ")
    text = text.replace("--", " ")
    text = text.replace("_", " ")
    text = text.replace(".", " ")
    text = text.replace("/", " ")
    text = text.replace("'", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for old, new in PHRASE_REPLACEMENTS:
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return re.sub(r"\s+", " ", text).strip()


def field_line(line: str) -> str:
    if ":" not in line:
        return simple_text(line)
    field, value = line.split(":", 1)
    clean_field = simple_text(field)
    clean_value = simple_text(value)
    if clean_value:
        return f"{clean_field}: {clean_value}"
    return f"{clean_field}:"


def id_tail(identifier: Any) -> str:
    return simple_text(str(identifier or "").split(".")[-1])


def load_nodes(source_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    dataset_manifest = load_json(source_dir / "datasets" / "manifest.json")
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]] = {}
    for graph_path in dataset_manifest.get("source_graphs", {}).values():
        graph = load_json(Path(graph_path))
        nodes_by_graph[graph["graph_id"]] = {
            node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and "id" in node
        }
    return nodes_by_graph


def node_words(_nodes: dict[str, dict[str, Any]], identifier: Any) -> str:
    if not isinstance(identifier, str) or not identifier:
        return ""
    if identifier in NODE_OVERRIDES:
        return simple_text(NODE_OVERRIDES[identifier])
    return id_tail(identifier)


def relation_words(rel_type: Any) -> str:
    rel = str(rel_type or "")
    return simple_text(RELATION_WORDS.get(rel, rel.replace("_", " ")))


def domain_words(example: Example) -> str:
    domain_id = example.get("metadata", {}).get("domain_id")
    return DOMAIN_WORDS.get(domain_id, simple_text(domain_id or "world"))


def task_words(example: Example) -> str:
    return TASK_WORDS.get(example.get("task_type", ""), "answer")


def field_value(text: str, field: str) -> str:
    pattern = re.compile(FIELD_RE_TEMPLATE.format(field=re.escape(field)), flags=re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return simple_text(match.group(1)) if match else ""


def question_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "QUESTION") or simple_text(example.get("input", ""))


def title_text(example: Example) -> str:
    return field_value(str(example.get("input", "")), "TITLE")


def event_text(example: Example) -> str:
    events: list[str] = []
    in_events = False
    for line in str(example.get("input", "")).splitlines():
        stripped = line.strip()
        if stripped.upper() == "EVENTS:":
            in_events = True
            continue
        if in_events and stripped.startswith("-"):
            events.append(simple_text(stripped.removeprefix("-")))
        elif in_events and stripped and not stripped.startswith("-"):
            break
    return " then ".join(event for event in events if event)


def relation_line(relation: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> str:
    source = node_words(nodes, relation.get("source"))
    link = relation_words(relation.get("type"))
    target = node_words(nodes, relation.get("target"))
    parts = []
    if source:
        parts.append(f"from: {source}")
    if link:
        parts.append(f"how: {link}")
    if target:
        parts.append(f"to: {target}")
    return " ; ".join(parts)


def relation_lines(relations: list[dict[str, Any]], nodes: dict[str, dict[str, Any]]) -> str:
    lines = [relation_line(relation, nodes) for relation in relations]
    lines = [line for line in lines if line]
    return "\n".join(f"link: {line}" for line in lines) if lines else "link: none"


def family_words(family_ids: list[Any], nodes: dict[str, dict[str, Any]]) -> str:
    words = [node_words(nodes, family_id) or id_tail(family_id) for family_id in family_ids]
    words = [word for word in words if word]
    return " ; ".join(words) if words else "none"


def answer_words(value: Any) -> str:
    text = simple_text(value)
    text = re.sub(r"\bthe hand is can move and produces direct feel\b", "baby can move hand and can feel hand", text)
    text = re.sub(r"\bproduces direct feel\b", "can feel", text)
    return simple_text(text)


def target_relations(example: Example) -> list[dict[str, Any]]:
    target = example.get("target", {})
    task_type = example["task_type"]
    if task_type == "relation_completion":
        return [{"source": target.get("source"), "type": target.get("type"), "target": target.get("target")}]
    if task_type == "state_action_effect":
        return target.get("relations_observed", [])
    if task_type == "counterfactual_contrast":
        relation = target.get("contrast_relation")
        return [relation] if isinstance(relation, dict) else []
    if task_type == "explanation_path":
        return target.get("expected_relations", [])
    if task_type in {"graph_anchor_from_prompt", "explanation_with_relations"}:
        return target.get("graph_anchors", [])
    return []


def answer_for(example: Example, nodes: dict[str, dict[str, Any]]) -> str:
    target = example.get("target", {})
    task_type = example["task_type"]
    if task_type == "relation_completion":
        return node_words(nodes, target.get("target"))
    if task_type == "state_action_effect":
        return relation_lines(target.get("relations_observed", []), nodes)
    if task_type == "counterfactual_contrast":
        relations = target_relations(example)
        if relations:
            source = node_words(nodes, relations[0].get("source"))
            target_word = node_words(nodes, relations[0].get("target"))
            return f"{source} is not like {target_word}".strip()
        return "it changes"
    if task_type == "explanation_path":
        return answer_words(target.get("expected_answer", example.get("text_target", "")))
    if task_type == "node_id_from_paraphrase":
        return node_words(nodes, target.get("node_id"))
    if task_type == "relation_family_from_prompt":
        return family_words(target.get("relation_family_ids", []), nodes)
    if task_type == "graph_anchor_from_prompt":
        return relation_lines(target.get("graph_anchors", []), nodes)
    if task_type == "explanation_with_relations":
        return answer_words(target.get("answer", example.get("text_target", "")))
    raise ValueError(f"unsupported task type: {task_type}")


def scene_for(example: Example, nodes: dict[str, dict[str, Any]]) -> str:
    target = example.get("target", {})
    task_type = example["task_type"]
    if task_type == "relation_completion":
        source = node_words(nodes, target.get("source"))
        link = relation_words(target.get("type"))
        return f"{source} {link}".strip()
    if task_type == "state_action_effect":
        title = title_text(example)
        events = event_text(example)
        return simple_text(f"{title} {events}") or "things happen"
    if task_type == "counterfactual_contrast":
        relations = target_relations(example)
        if relations:
            source = node_words(nodes, relations[0].get("source"))
            target_word = node_words(nodes, relations[0].get("target"))
            return f"{source} and {target_word}".strip()
        return "two things"
    if task_type in {"explanation_path", "explanation_with_relations", "relation_family_from_prompt"}:
        return question_text(example)
    if task_type == "node_id_from_paraphrase":
        return node_words(nodes, target.get("node_id"))
    if task_type == "graph_anchor_from_prompt":
        relations = target.get("graph_anchors", [])
        if relations:
            return " ".join(
                " ".join(
                    part for part in (
                        node_words(nodes, relation.get("source")),
                        relation_words(relation.get("type")),
                        node_words(nodes, relation.get("target")),
                    )
                    if part
                )
                for relation in relations
            )
        return question_text(example)
    return simple_text(example.get("input", ""))


def ask_for(example: Example) -> str:
    task_type = example["task_type"]
    if task_type == "relation_completion":
        return "what comes next"
    if task_type == "state_action_effect":
        return "what changed"
    if task_type == "counterfactual_contrast":
        return "what is not the same"
    if task_type in {"explanation_path", "explanation_with_relations"}:
        return "why"
    if task_type == "node_id_from_paraphrase":
        return "what is it"
    if task_type == "relation_family_from_prompt":
        return "what kind"
    if task_type == "graph_anchor_from_prompt":
        return "what link"
    return "answer"


def child_input(example: Example, nodes: dict[str, dict[str, Any]], want_links: bool = False) -> str:
    lines = [
        f"do: {task_words(example)}",
        f"world: {domain_words(example)}",
        f"scene: {scene_for(example, nodes)}",
        f"ask: {ask_for(example)}",
    ]
    if want_links:
        links = relation_lines(target_relations(example), nodes)
        lines.append("links:")
        lines.extend(links.splitlines())
    lines.append("answer:")
    return "\n".join(field_line(line) for line in lines)


def child_target(example: Example, nodes: dict[str, dict[str, Any]], include_links: bool = False) -> str:
    answer = answer_for(example, nodes)
    if "\n" in answer and answer.startswith("link:"):
        lines = ["answer: links"]
        lines.extend(answer.splitlines())
    else:
        lines = [f"answer: {answer}"]
    if include_links and not (answer.startswith("link:") or "\nlink:" in answer):
        links = relation_lines(target_relations(example), nodes)
        if links.strip() != "link: none":
            lines.append("links:")
            lines.extend(links.splitlines())
    return "\n".join(field_line(line) for line in lines)


def render_pair(variant: str, example: Example, nodes: dict[str, dict[str, Any]]) -> tuple[str, str]:
    if variant == "child_plain_text":
        return child_input(example, nodes, want_links=False), child_target(example, nodes, include_links=False)
    if variant == "child_relation_scaffolded":
        return child_input(example, nodes, want_links=False), child_target(example, nodes, include_links=True)
    if variant == "child_relation_first_then_text":
        return child_input(example, nodes, want_links=True), child_target(example, nodes, include_links=False)
    raise ValueError(f"unknown variant: {variant}")


def make_record(
    experiment_id: str,
    variant: str,
    split_name: str,
    example: Example,
    nodes_by_graph: dict[str, dict[str, dict[str, Any]]],
) -> Record:
    graph_id = example.get("graph_id")
    nodes = nodes_by_graph.get(graph_id, {})
    input_text, target_text = render_pair(variant, example, nodes)
    if not input_text.strip() or not target_text.strip():
        raise ValueError(f"empty child-language record for {variant}/{example['id']}")
    return {
        "id": f"dataset.{experiment_id}.{variant}.{example['id']}",
        "source_example_id": example["id"],
        "experiment_id": experiment_id,
        "variant": variant,
        "split": split_name,
        "task_type": example["task_type"],
        "input": input_text,
        "target": target_text,
        "messages": [
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": target_text},
        ],
        "metadata": {
            "domain_id": example.get("metadata", {}).get("domain_id"),
            "domain_label": example.get("metadata", {}).get("domain_label"),
            "graph_id": graph_id,
            "representation": variant,
            "source_representation": "core5_v0",
            "vocabulary_policy": "child_language_colon_fields",
        },
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(key, "unknown") for row in rows).items()))


def domain_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row.get("metadata", {}).get("domain_id", "unknown") for row in rows).items()))


def vocab_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    words: Counter[str] = Counter()
    raw: Counter[str] = Counter()
    for row in rows:
        text = f"{row.get('input', '')}\n{row.get('target', '')}".lower()
        words.update(WORD_RE.findall(text))
        raw.update(RAW_RE.findall(text))
    return {
        "unique_words_alpha": len(words),
        "total_words_alpha": sum(words.values()),
        "unique_raw_whitespace_tokens": len(raw),
        "total_raw_whitespace_tokens": sum(raw.values()),
        "top_words": dict(words.most_common(40)),
    }


def validate_matched(records: dict[str, dict[str, list[Record]]]) -> None:
    for split_name in SPLITS:
        expected: set[str] | None = None
        for variant in VARIANTS:
            source_ids = {row["source_example_id"] for row in records[variant][split_name]}
            if expected is None:
                expected = source_ids
            elif source_ids != expected:
                missing = sorted(expected - source_ids)[:5]
                extra = sorted(source_ids - expected)[:5]
                raise ValueError(f"{split_name}/{variant} source mismatch missing={missing} extra={extra}")


def file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(paths.items())
    }


def build_training_config(experiment_id: str, output_dir: Path, dataset_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "experiment_id": experiment_id,
        "baseline_model": {
            "name": "HuggingFaceTB/SmolLM2-135M",
            "role": "format validation only before nanochat from-scratch training",
            "reason": "Use dry-run compatibility checks; actual child-language test should use nanochat.",
        },
        "dataset_manifest": str(dataset_manifest),
        "output_root": f"runs/{experiment_id}/smollm2_135m",
        "format": {
            "prompt_template": "{input}\n",
            "target_template": "{target}",
        },
        "training": {
            "max_seq_length": 512,
            "num_train_epochs": 3,
            "learning_rate": 5e-5,
            "per_device_train_batch_size": 1,
            "per_device_eval_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "warmup_ratio": 0.03,
            "weight_decay": 0.0,
            "logging_steps": 10,
            "save_total_limit": 2,
            "seed": 1729,
        },
        "frozen_commands": {
            variant: f"python3 scripts/train_tiny_causal_lm.py --config {output_dir / 'training_config.json'} --variant {variant} --dry-run"
            for variant in VARIANTS
        },
        "notes": [
            "This config is for JSONL format checks only.",
            "The intended training path is nanochat from scratch with a shared tokenizer.",
        ],
    }


def copy_if_exists(source: Path, target: Path) -> Path | None:
    if not source.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/developmental_graph/experiments/core5_v0"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/developmental_graph/experiments/core5_v0_childlang"))
    parser.add_argument("--experiment-id", default="core5_v0_childlang")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir, args.overwrite)
    nodes_by_graph = load_nodes(args.source_dir)
    split_examples = {split: load_jsonl(args.source_dir / f"{split}.jsonl") for split in SPLITS}
    for split_name, rows in split_examples.items():
        write_jsonl(args.output_dir / f"{split_name}.jsonl", rows)

    records: dict[str, dict[str, list[Record]]] = {
        variant: {split_name: [] for split_name in SPLITS}
        for variant in VARIANTS
    }
    dataset_paths: dict[str, Path] = {}
    for variant in VARIANTS:
        for split_name in SPLITS:
            rows = [
                make_record(args.experiment_id, variant, split_name, example, nodes_by_graph)
                for example in split_examples[split_name]
            ]
            records[variant][split_name] = rows
            path = args.output_dir / "datasets" / variant / f"{split_name}.jsonl"
            write_jsonl(path, rows)
            dataset_paths[f"{variant}.{split_name}"] = path

    validate_matched(records)

    copied_paths: dict[str, Path] = {}
    for name in ("heldout.json", "heldout_prompts.jsonl"):
        copied = copy_if_exists(args.source_dir / name, args.output_dir / name)
        if copied:
            copied_paths[name.removesuffix(".json").removesuffix(".jsonl")] = copied

    dataset_manifest_path = args.output_dir / "datasets" / "manifest.json"
    dataset_manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "output_dir": str(args.output_dir / "datasets"),
        "variants": {
            variant: {
                split_name: {
                    "total": len(records[variant][split_name]),
                    "task_type_counts": count_by(records[variant][split_name], "task_type"),
                    "domain_counts": domain_counts(records[variant][split_name]),
                    "vocabulary": vocab_stats(records[variant][split_name]),
                }
                for split_name in SPLITS
            }
            for variant in VARIANTS
        },
        "outputs": file_manifest(dataset_paths),
        "notes": [
            "All variants preserve source_example_id and split membership from core5_v0.",
            "Fields are colon-delimited instead of JSON.",
            "Technical relation words are rewritten into simpler child-language words where possible.",
        ],
    }
    write_json(dataset_manifest_path, dataset_manifest)

    vocabulary_dir = args.output_dir / "vocabulary"
    vocabulary_dir.mkdir(parents=True, exist_ok=True)
    all_train_words: Counter[str] = Counter()
    for variant in VARIANTS:
        for row in records[variant]["train"]:
            all_train_words.update(WORD_RE.findall(f"{row['input']}\n{row['target']}".lower()))
    alpha_vocab_path = vocabulary_dir / "train_alpha_words.txt"
    alpha_vocab_path.write_text("\n".join(sorted(all_train_words)) + "\n")

    training_config_path = args.output_dir / "training_config.json"
    write_json(training_config_path, build_training_config(args.experiment_id, args.output_dir, dataset_manifest_path))

    output_paths = {
        **dataset_paths,
        "dataset_manifest": dataset_manifest_path,
        "training_config": training_config_path,
        "train_alpha_words": alpha_vocab_path,
    }
    output_paths.update(copied_paths)
    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.experiment_id,
        "source_experiment_dir": str(args.source_dir),
        "source_manifest": str(args.source_dir / "manifest.json"),
        "child_language_policy": {
            "case": "lowercase",
            "fields": "colon_delimited",
            "json_targets": "removed",
            "technical_words": "rewritten_when_possible",
            "relation_words": "from_link_to",
        },
        "splits": {
            split_name: {
                "total": len(split_examples[split_name]),
                "task_type_counts": count_by(split_examples[split_name], "task_type"),
            }
            for split_name in SPLITS
        },
        "variants": list(VARIANTS),
        "vocabulary": {
            "train_unique_words_all_variants": len(all_train_words),
            "train_alpha_words_path": str(alpha_vocab_path),
        },
        "dataset_manifest": str(dataset_manifest_path),
        "training_config": str(training_config_path),
        "outputs": file_manifest(output_paths),
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
