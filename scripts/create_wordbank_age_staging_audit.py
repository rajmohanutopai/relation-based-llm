#!/usr/bin/env python3
"""Create a Wordbank/CDI age-staging audit for the developmental vocabulary.

Wordbank is not used as a relation source. It is used to check whether words in
our age-layered concept lists are developmentally early or late according to
MacArthur-Bates CDI data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from create_age_6mo_conceptnet_relation_dataset import (
    DEFAULT_SEED,
    build_aliases,
    load_seed_words,
    load_source_aliases,
    map_word,
)


GITHUB_API = "https://api.github.com/repos/langcog/wordbank/contents/raw_data/{dataset}?ref=master"
RAW_BASE = "https://raw.githubusercontent.com/langcog/wordbank/master/raw_data/{dataset}/{name}"
DATASETS = {
    "English_American_WG": "WG",
    "English_American_WS": "WS",
}
ITEM_FILES = {
    "WG": "English_American_WG.csv",
    "WS": "English_American_WS.csv",
}
ITEM_URLS = {
    "WG": "https://raw.githubusercontent.com/langcog/wordbank/master/raw_data/English_American_WG/%5BEnglish_WG%5D.csv",
    "WS": "https://raw.githubusercontent.com/langcog/wordbank/master/raw_data/English_American_WS/%5BEnglish_WS%5D.csv",
}

DEFAULT_EXTERNAL = Path("data/external/wordbank")
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/wordbank_age_staging_v0")


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    path.write_bytes(response.content)


def list_dataset_files(dataset: str) -> list[dict[str, Any]]:
    response = requests.get(GITHUB_API.format(dataset=dataset), timeout=30)
    response.raise_for_status()
    return response.json()


def download_wordbank(external_dir: Path) -> dict[str, list[Path]]:
    downloaded: dict[str, list[Path]] = {}
    for form, url in ITEM_URLS.items():
        download(url, external_dir / ITEM_FILES[form])
    for dataset, form in DATASETS.items():
        dataset_dir = external_dir / "raw_data" / dataset
        files: list[Path] = []
        for item in list_dataset_files(dataset):
            name = item["name"]
            if not name.endswith(("_data.csv", "_fields.csv")):
                continue
            path = dataset_dir / name
            download(RAW_BASE.format(dataset=dataset, name=name), path)
            files.append(path)
        downloaded[form] = files
    return downloaded


def normalize_word(word: str | float | None) -> str | None:
    if word is None or pd.isna(word):
        return None
    word = str(word).lower().strip()
    word = word.replace("_", " ")
    word = word.replace(".", " ")
    word = re.sub(r"\b(a|an|the)\b", " ", word)
    word = re.sub(r"[^a-z' ]+", " ", word)
    word = re.sub(r"\s+", " ", word).strip()
    return word or None


def read_items(external_dir: Path) -> dict[str, pd.DataFrame]:
    items = {}
    for form, filename in ITEM_FILES.items():
        df = pd.read_csv(external_dir / filename)
        df["wordbank_form"] = form
        df["word"] = df["gloss"].map(normalize_word)
        items[form] = df
    return items


def value_bool(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    return numeric > 0


def age_series(df: pd.DataFrame) -> pd.Series:
    for col in ["data_age", "calccdiage", "cdiage", "age"]:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
    raise ValueError("No age column found")


def matching_column(df: pd.DataFrame, column: str) -> str | None:
    if column in df.columns:
        return column
    lower = {col.lower(): col for col in df.columns}
    return lower.get(column.lower())


def summarize_form(form: str, external_dir: Path, min_age_n: int) -> pd.DataFrame:
    dataset_name = next(name for name, dataset_form in DATASETS.items() if dataset_form == form)
    raw_dir = external_dir / "raw_data" / dataset_name
    item_file = external_dir / ITEM_FILES[form]
    item_lookup = pd.read_csv(item_file)
    item_by_id = item_lookup.set_index("itemID").to_dict("index")
    accum: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)
    file_count = 0

    for fields_path in sorted(raw_dir.glob("*_fields.csv")):
        data_path = fields_path.with_name(fields_path.name.replace("_fields.csv", "_data.csv"))
        if not data_path.exists():
            continue
        fields = pd.read_csv(fields_path)
        fields = fields[(fields["group"] == "item") & (fields["type"] == "word")]
        if fields.empty:
            continue
        data = pd.read_csv(data_path, low_memory=False)
        try:
            ages = age_series(data)
        except ValueError:
            continue
        valid_age = ages.notna()
        file_count += 1
        for _, field in fields.iterrows():
            item_id = str(field["field"])
            item_meta = item_by_id.get(item_id)
            if not item_meta:
                continue
            base_column = str(field["column"])
            word = normalize_word(item_meta.get("gloss") or item_meta.get("item"))
            category = item_meta.get("category")
            if not word:
                continue
            if form == "WG":
                produce_col = matching_column(data, f"{base_column}p")
                understand_col = matching_column(data, f"{base_column}u")
                if not produce_col and not understand_col:
                    continue
                produces = value_bool(data[produce_col]) if produce_col else pd.Series(False, index=data.index)
                understands = value_bool(data[understand_col]) if understand_col else pd.Series(False, index=data.index)
                understands = understands | produces
            else:
                produce_col = matching_column(data, base_column)
                if not produce_col:
                    continue
                produces = value_bool(data[produce_col])
                understands = produces.copy()
            for age in sorted(ages[valid_age].dropna().astype(int).unique()):
                mask = valid_age & (ages.astype("Int64") == age)
                n = int(mask.sum())
                if n == 0:
                    continue
                key = (word, int(age))
                accum[key]["n"] += n
                accum[key]["produces"] += int(produces[mask].sum())
                accum[key]["understands"] += int(understands[mask].sum())
                accum[key]["category"] = category

    rows = []
    by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (word, age), counts in accum.items():
        n = counts["n"]
        if n < min_age_n:
            continue
        item = {
            "word": word,
            "form": form,
            "age_months": age,
            "n": n,
            "understands_prop": counts["understands"] / n,
            "produces_prop": counts["produces"] / n,
            "category": counts.get("category"),
        }
        by_word[word].append(item)

    for word, age_rows in by_word.items():
        age_rows = sorted(age_rows, key=lambda row: row["age_months"])
        category = next((row["category"] for row in age_rows if row.get("category")), None)
        rows.append({
            "word": word,
            "form": form,
            "category": category,
            "min_age": min(row["age_months"] for row in age_rows),
            "max_age": max(row["age_months"] for row in age_rows),
            "aoa_understands_50": first_age(age_rows, "understands_prop", 0.5),
            "aoa_understands_25": first_age(age_rows, "understands_prop", 0.25),
            "aoa_produces_50": first_age(age_rows, "produces_prop", 0.5),
            "aoa_produces_25": first_age(age_rows, "produces_prop", 0.25),
            "max_understands_prop": max(row["understands_prop"] for row in age_rows),
            "max_produces_prop": max(row["produces_prop"] for row in age_rows),
            "age_points": len(age_rows),
            "source_files": file_count,
        })
    return pd.DataFrame(rows).sort_values(["form", "aoa_understands_25", "aoa_produces_25", "word"], na_position="last")


def first_age(age_rows: list[dict[str, Any]], field: str, threshold: float) -> int | None:
    for row in age_rows:
        if row[field] >= threshold:
            return int(row["age_months"])
    return None


def match_seed(wordbank: pd.DataFrame, seed_path: Path, source_aliases_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    seed_words, concepts = load_seed_words(seed_path)
    source_aliases = load_source_aliases(source_aliases_path, seed_words)
    aliases = build_aliases(seed_words, concepts, source_aliases)
    matched = []
    unmatched = []
    for row in wordbank.to_dict("records"):
        mapped = map_word(row["word"], aliases)
        output = dict(row)
        output["seed_word"] = mapped
        output["seed_category"] = concepts[mapped]["category"] if mapped else None
        if mapped:
            matched.append(output)
        else:
            unmatched.append(output)
    return pd.DataFrame(matched), pd.DataFrame(unmatched), len(source_aliases)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-dir", type=Path, default=DEFAULT_EXTERNAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--min-age-n", type=int, default=10)
    parser.add_argument("--source-aliases", type=Path)
    args = parser.parse_args()

    downloaded = download_wordbank(args.external_dir)
    summaries = [
        summarize_form("WG", args.external_dir, args.min_age_n),
        summarize_form("WS", args.external_dir, args.min_age_n),
    ]
    wordbank = pd.concat(summaries, ignore_index=True)
    matched, unmatched, source_alias_count = match_seed(wordbank, args.seed_path, args.source_aliases)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    wordbank.to_csv(args.output_dir / "wordbank_english_american_item_staging.csv", index=False)
    matched.to_csv(args.output_dir / "seed_matches.csv", index=False)
    unmatched.to_csv(args.output_dir / "unmatched_wordbank_items.csv", index=False)

    early_unmatched = unmatched[
        (unmatched["aoa_understands_50"].fillna(999) <= 16)
        | (unmatched["aoa_produces_25"].fillna(999) <= 18)
    ].sort_values(["aoa_understands_50", "aoa_produces_25", "word"], na_position="last")
    early_unmatched.to_csv(args.output_dir / "early_unmatched_wordbank_items.csv", index=False)

    manifest = {
        "schema_version": "0.1.0",
        "experiment_id": args.output_dir.name,
        "source": "Wordbank / MacArthur-Bates CDI raw English American WG and WS files",
        "license_note": "Wordbank datasets are published under CC-BY 4.0 unless otherwise stated by Wordbank.",
        "external_dir": str(args.external_dir),
        "seed_path": str(args.seed_path),
        "min_age_n": args.min_age_n,
        "source_aliases_path": str(args.source_aliases) if args.source_aliases else None,
        "source_aliases_loaded": source_alias_count,
        "downloaded_files": {form: len(paths) for form, paths in downloaded.items()},
        "wordbank_items": len(wordbank),
        "matched_rows": len(matched),
        "matched_seed_concepts": int(matched["seed_word"].nunique()) if not matched.empty else 0,
        "unmatched_rows": len(unmatched),
        "early_unmatched_rows": len(early_unmatched),
        "forms": dict(sorted(Counter(wordbank["form"]).items())),
        "notes": [
            "This is an age-staging audit, not a relation dataset.",
            "WG contributes receptive and expressive estimates; WS contributes expressive estimates.",
            "AoA columns are approximate first ages where the observed proportion crosses the threshold.",
            "Use early unmatched items to revise age-layer vocabulary, not as automatic additions.",
        ],
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
