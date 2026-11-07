#!/usr/bin/env python3
"""Embedding-based nearest-source audit for uncovered seed concepts."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from nltk.corpus import wordnet as wn
from transformers import AutoModel, AutoTokenizer


DEFAULT_SEED = Path("data/developmental_graph/seeds/age_6mo_root_world_wordbank_v1.json")
DEFAULT_EDGES = Path("data/developmental_graph/experiments/age_6mo_external_relations_v4_wordbank_seed/edges.all.jsonl")
DEFAULT_CONCEPTNET = Path("data/external/conceptnet/conceptnet-assertions-5.7.0-en-en.tsv")
DEFAULT_VG_DIR = Path("data/external/visual_genome")
DEFAULT_WORDBANK_DIR = Path("data/external/wordbank")
DEFAULT_VG_EDGES = Path("data/developmental_graph/experiments/age_6mo_visual_genome_relations_v4_wordbank_seed/edges.all.jsonl")
DEFAULT_EXTERNAL_EDGES = Path("data/developmental_graph/experiments/age_6mo_external_relations_v4_wordbank_seed/edges.all.jsonl")
DEFAULT_OUTPUT = Path("data/developmental_graph/experiments/seed_embedding_source_audit_v0")
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def norm(text: str | None) -> str | None:
    if text is None or pd.isna(text):
        return None
    text = str(text)
    if not text:
        return None
    text = text.lower().strip().replace("_", " ")
    text = re.sub(r"^/c/en/", "", text)
    text = re.sub(r"/.*$", "", text)
    text = re.sub(r"[^a-z' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text or len(text) <= 1:
        return None
    return text


def conceptnet_word(uri: str) -> str | None:
    if not uri.startswith("/c/en/"):
        return None
    return norm(uri.split("/")[3])


def load_uncovered(seed_path: Path, edges_path: Path, sample_size: int, seed: int, all_uncovered: bool) -> list[dict]:
    data = json.loads(seed_path.read_text())
    covered = set()
    for line in edges_path.open():
        row = json.loads(line)
        covered.add(row["start"])
        covered.add(row["end"])
    uncovered = [item for item in data["concepts"] if item["word"] not in covered]
    if all_uncovered:
        return uncovered
    rng = random.Random(seed)
    return rng.sample(uncovered, min(sample_size, len(uncovered)))


def add_vocab(vocab: dict[str, set[str]], source: str, terms: Iterable[str | None]) -> None:
    for term in terms:
        cleaned = norm(term)
        if cleaned:
            vocab[cleaned].add(source)


def query_terms(sample: list[dict]) -> set[str]:
    terms: set[str] = set()
    for item in sample:
        for part in [item["word"], *item.get("aliases", [])]:
            cleaned = norm(part)
            if not cleaned:
                continue
            terms.add(cleaned)
            terms.update(token for token in cleaned.split() if len(token) >= 3)
    return terms


def query_index(queries: set[str]) -> tuple[set[str], set[str]]:
    tokens = set()
    phrases = set()
    for query in queries:
        cleaned = norm(query)
        if not cleaned:
            continue
        phrases.add(cleaned)
        tokens.update(token for token in cleaned.split() if len(token) >= 3)
    return phrases, tokens


def near_query(term: str | None, queries: set[str]) -> bool:
    cleaned = norm(term)
    if not cleaned:
        return False
    if cleaned in queries:
        return True
    tokens = set(cleaned.split())
    return any(query in cleaned or cleaned in query or query in tokens for query in queries)


def near_query_index(term: str | None, phrases: set[str], tokens: set[str]) -> bool:
    cleaned = norm(term)
    if not cleaned:
        return False
    if cleaned in phrases:
        return True
    term_tokens = {token for token in cleaned.split() if len(token) >= 3}
    if term_tokens & tokens:
        return True
    return False


def collect_conceptnet(path: Path, vocab: dict[str, set[str]], queries: set[str]) -> int:
    count = 0
    phrases, tokens = query_index(queries)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            start = conceptnet_word(parts[2])
            end = conceptnet_word(parts[3])
            if near_query_index(start, phrases, tokens) or near_query_index(end, phrases, tokens):
                add_vocab(vocab, "conceptnet", [start, end])
            count += 1
    return count


def collect_wordnet(vocab: dict[str, set[str]], queries: set[str]) -> int:
    count = 0
    phrases, tokens = query_index(queries)
    for synset in wn.all_synsets():
        lemmas = [lemma.replace("_", " ") for lemma in synset.lemma_names()]
        definition = synset.definition()
        if any(near_query_index(lemma, phrases, tokens) for lemma in lemmas) or near_query_index(definition, phrases, tokens):
            add_vocab(vocab, "wordnet", lemmas)
            add_vocab(vocab, "wordnet", [definition])
            count += 1
    return count


def read_zip_json(path: Path):
    with zipfile.ZipFile(path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as handle:
            return json.load(handle)


def collect_visual_genome(vg_dir: Path, vg_edges: Path, vocab: dict[str, set[str]], queries: set[str]) -> int:
    count = 0
    phrases, tokens = query_index(queries)
    for alias_file in ["object_alias.txt", "relationship_alias.txt"]:
        path = vg_dir / alias_file
        if path.exists():
            for line in path.open(encoding="utf-8"):
                terms = line.rstrip("\n").split(",")
                if any(near_query_index(term, phrases, tokens) for term in terms):
                    add_vocab(vocab, "visual_genome", terms)
                count += 1
    if vg_edges.exists():
        for line in vg_edges.open():
            row = json.loads(line)
            terms = [row["start"], row["end"]]
            if near_query_index(row["start"], phrases, tokens) or near_query_index(row["end"], phrases, tokens):
                add_vocab(vocab, "visual_genome", terms)
            count += 1
    return count


def collect_wordbank(wordbank_dir: Path, vocab: dict[str, set[str]], queries: set[str]) -> int:
    count = 0
    phrases, tokens = query_index(queries)
    for path in [wordbank_dir / "English_American_WG.csv", wordbank_dir / "English_American_WS.csv"]:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for col in ["item", "definition", "gloss", "uni_lemma", "category"]:
            if col in df:
                terms = [term for term in df[col].tolist() if near_query_index(str(term), phrases, tokens)]
                add_vocab(vocab, "wordbank", terms)
        count += len(df)
    return count


def collect_existing_edges(path: Path, vocab: dict[str, set[str]], queries: set[str]) -> int:
    count = 0
    phrases, tokens = query_index(queries)
    if not path.exists():
        return count
    for line in path.open():
        row = json.loads(line)
        terms = [row["start"], row["end"]]
        if near_query_index(row["start"], phrases, tokens) or near_query_index(row["end"], phrases, tokens):
            add_vocab(vocab, row.get("source", "external_edges"), terms)
        count += 1
    return count


def describe_query(item: dict) -> str:
    parts = [item["word"], item.get("summary", "")]
    for alias in item.get("aliases", []):
        parts.append(alias)
    for rel in item.get("relations", [])[:3]:
        parts.append(rel.get("text", ""))
    return ". ".join(part for part in parts if part)


def lexical_score(query: str, term: str) -> float:
    q = norm(query) or ""
    t = norm(term) or ""
    if not q or not t:
        return 0.0
    q_tokens = set(q.split())
    t_tokens = set(t.split())
    overlap = len(q_tokens & t_tokens) / max(1, len(q_tokens | t_tokens))
    substring = 1.0 if q in t or t in q else 0.0
    q_chars = {chunk for chunk in zip(q, q[1:], q[2:])}
    t_chars = {chunk for chunk in zip(t, t[1:], t[2:])}
    char_overlap = len(q_chars & t_chars) / max(1, len(q_chars | t_chars))
    return max(overlap, substring, char_overlap * 0.85)


def prefilter_candidates(
    sample: list[dict],
    source_terms: list[str],
    per_query: int,
) -> tuple[list[str], dict[str, list[str]]]:
    selected: set[str] = set()
    by_query: dict[str, list[str]] = {}
    for item in sample:
        query = item["word"]
        scored = []
        for term in source_terms:
            score = lexical_score(query, term)
            if score >= 0.25:
                scored.append((score, term))
        scored.sort(reverse=True)
        terms = [term for _, term in scored[:per_query]]
        by_query[query] = terms
        selected.update(terms)
    return sorted(selected), by_query


def prefilter_candidates_fast(
    sample: list[dict],
    source_terms: list[str],
    per_query: int,
) -> tuple[list[str], dict[str, list[str]]]:
    selected: set[str] = set()
    by_query: dict[str, list[str]] = {}
    query_parts = {}
    for item in sample:
        word = norm(item["word"]) or item["word"]
        tokens = {token for token in word.split() if len(token) >= 3}
        aliases = {norm(alias) for alias in item.get("aliases", [])}
        aliases = {alias for alias in aliases if alias}
        query_parts[item["word"]] = (word, tokens, aliases)

    for item in sample:
        word, tokens, aliases = query_parts[item["word"]]
        candidates = []
        for term in source_terms:
            term_norm = norm(term) or ""
            term_tokens = set(term_norm.split())
            score = 0.0
            if term_norm == word or term_norm in aliases:
                score = 1.0
            elif word in term_norm or term_norm in word:
                score = 0.9
            elif tokens & term_tokens:
                score = 0.65 + (len(tokens & term_tokens) / max(10, len(tokens | term_tokens)))
            elif any(alias in term_norm or term_norm in alias for alias in aliases):
                score = 0.7
            if score:
                candidates.append((score, term))
        candidates.sort(reverse=True)
        terms = [term for _, term in candidates[:per_query]]
        by_query[item["word"]] = terms
        selected.update(terms)
    return sorted(selected), by_query


def embed_texts(texts: list[str], model_name: str, batch_size: int) -> np.ndarray:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    outputs = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=96, return_tensors="pt")
            model_out = model(**encoded)
            token_embeddings = model_out.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
            pooled = (token_embeddings * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            outputs.append(pooled.cpu().numpy())
    return np.vstack(outputs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--edges-path", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--conceptnet-path", type=Path, default=DEFAULT_CONCEPTNET)
    parser.add_argument("--vg-dir", type=Path, default=DEFAULT_VG_DIR)
    parser.add_argument("--vg-edges", type=Path, default=DEFAULT_VG_EDGES)
    parser.add_argument("--external-edges", type=Path, default=DEFAULT_EXTERNAL_EDGES)
    parser.add_argument("--wordbank-dir", type=Path, default=DEFAULT_WORDBANK_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--all-uncovered", action="store_true")
    parser.add_argument("--random-seed", type=int, default=20260501)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--prefilter-per-query", type=int, default=800)
    parser.add_argument("--slow-prefilter", action="store_true")
    args = parser.parse_args()

    sample = load_uncovered(args.seed_path, args.edges_path, args.sample_size, args.random_seed, args.all_uncovered)
    vocab: dict[str, set[str]] = defaultdict(set)
    queries = query_terms(sample)
    source_counts = {
        "conceptnet_lines_scanned": collect_conceptnet(args.conceptnet_path, vocab, queries),
        "wordnet_synsets_scanned": collect_wordnet(vocab, queries),
        "visual_genome_items_scanned": collect_visual_genome(args.vg_dir, args.vg_edges, vocab, queries),
        "wordbank_rows_scanned": collect_wordbank(args.wordbank_dir, vocab, queries),
        "existing_external_edges_scanned": collect_existing_edges(args.external_edges, vocab, queries),
    }
    source_terms = sorted(vocab)
    query_texts = [describe_query(item) for item in sample]
    query_labels = [item["word"] for item in sample]

    if args.slow_prefilter:
        candidate_terms, prefilter_by_query = prefilter_candidates(sample, source_terms, args.prefilter_per_query)
    else:
        candidate_terms, prefilter_by_query = prefilter_candidates_fast(sample, source_terms, args.prefilter_per_query)
    all_texts = query_texts + candidate_terms
    embeddings = embed_texts(all_texts, args.model, args.batch_size)
    query_embeddings = embeddings[: len(query_texts)]
    source_embeddings = embeddings[len(query_texts):]
    scores = query_embeddings @ source_embeddings.T

    rows = []
    for i, item in enumerate(sample):
        order = np.argsort(-scores[i])[: args.top_k]
        for rank, j in enumerate(order, start=1):
            term = candidate_terms[int(j)]
            rows.append({
                "seed_word": query_labels[i],
                "seed_category": item["category"],
                "rank": rank,
                "candidate_phrase": term,
                "embedding_score": float(scores[i, j]),
                "sources": ",".join(sorted(vocab[term])),
                "approved": "",
                "approved_target": query_labels[i],
                "review_notes": "",
                "query_text": query_texts[i],
            })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "sampled_uncovered_concepts.json").open("w", encoding="utf-8") as handle:
        json.dump(sample, handle, indent=2, sort_keys=True)
    with (args.output_dir / "embedding_matches.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.output_dir / "source_mapping_review.csv").open("w", newline="", encoding="utf-8") as handle:
        review_fields = [
            "seed_word",
            "seed_category",
            "candidate_phrase",
            "sources",
            "embedding_score",
            "approved",
            "approved_target",
            "review_notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=review_fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in review_fields} for row in rows)
    manifest = {
        "experiment_id": args.output_dir.name,
        "seed_path": str(args.seed_path),
        "edges_path": str(args.edges_path),
        "model": args.model,
        "sample_size": len(sample),
        "all_uncovered": args.all_uncovered,
        "random_seed": args.random_seed,
        "source_terms": len(source_terms),
        "embedded_candidate_terms": len(candidate_terms),
        "prefilter_per_query": args.prefilter_per_query,
        "source_counts": source_counts,
        "notes": [
            "Queries are sampled from currently uncovered seed concepts.",
            "Query embedding text includes word, summary, aliases, and first relation texts.",
            "Source vocabulary includes source terms only, not full triples.",
            "Scores are cosine similarity from normalized sentence embeddings.",
        ],
    }
    with (args.output_dir / "prefilter_candidates.json").open("w", encoding="utf-8") as handle:
        json.dump(prefilter_by_query, handle, indent=2, sort_keys=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
