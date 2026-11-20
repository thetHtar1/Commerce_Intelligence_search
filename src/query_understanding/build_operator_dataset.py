"""Build reproducible query-to-intent examples from the operator phrase catalog."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "training" / "expression_understanding"
LEXICON_PATH = DATA_DIR / "operator_phrase_lexicon.csv"
OUTPUT_CSV = DATA_DIR / "operator_phrase_examples.csv"
OUTPUT_JSONL = DATA_DIR / "operator_phrase_examples.jsonl"
MANIFEST_PATH = DATA_DIR / "operator_phrase_manifest.json"
VALID_OPERATORS = {"lt", "lte", "gt", "gte", "eq", "between", "near"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _read_lexicon(path: Path = LEXICON_PATH) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _category(query: str) -> str | None:
    lowered = query.casefold()
    for phrase in ("running shoes", "shampoo", "monitor"):
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", lowered):
            return phrase
    return None


def _field_and_unit(query: str) -> tuple[str, str | None]:
    lowered = query.casefold()
    if re.search(r"\bbaht\b", lowered):
        return "price", "THB"
    if re.search(r"\bkg\b", lowered):
        return "weight", "kg"
    if re.search(r"\binches?\b", lowered):
        return "size", "inches"
    if re.search(r"\bstars?\b", lowered):
        return "rating", "stars"
    return "price", None


def _source_text(query: str, row: dict[str, str]) -> str:
    phrase = row["phrase"].casefold()
    lowered = query.casefold()
    phrase_start = lowered.find(phrase)
    if phrase_start < 0:
        raise ValueError(f"Phrase {phrase!r} is absent from its example: {query!r}")
    unit_match = re.search(r"\b(?:baht|kg|inches?|stars?)\b", query[phrase_start:], re.IGNORECASE)
    if row["position"] == "prefix":
        if unit_match:
            end = phrase_start + unit_match.end()
        else:
            end = phrase_start + len(phrase)
        return query[phrase_start:end]

    number_matches = list(re.finditer(r"\d[\d,]*(?:\.\d+)?", query[:phrase_start]))
    if not number_matches:
        raise ValueError(f"No amount occurs before suffix operator {phrase!r} in {query!r}")
    number_start = number_matches[-1].start()
    return query[number_start:phrase_start + len(phrase)]


def _expected_intent(
    query: str,
    constraints: list[dict[str, Any]] | None = None,
    soft_preferences: list[dict[str, Any]] | None = None,
    attributes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "original_query": query,
        "normalized_query": " ".join(query.casefold().split()),
        "language": "en",
        "query_type": "natural_language",
        "product_category": _category(query),
        "attributes": attributes or [],
        "constraints": constraints or [],
        "soft_preferences": soft_preferences or [],
        "ambiguities": [],
        "needs_clarification": False,
    }


def _numeric_example(row: dict[str, str]) -> dict[str, Any]:
    query = row["example_template"]
    operator = row["canonical_operator"]
    amount_matches = [float(value.replace(",", "")) for value in re.findall(r"\d[\d,]*(?:\.\d+)?", query)]
    if operator == "between":
        if len(amount_matches) != 2:
            raise ValueError(f"Range example must contain two values: {query!r}")
        value: Any = {"min": int(amount_matches[0]), "max": int(amount_matches[1])}
    else:
        if not amount_matches:
            raise ValueError(f"Numeric example has no amount: {query!r}")
        value = int(amount_matches[0]) if amount_matches[0].is_integer() else amount_matches[0]
    field, unit = _field_and_unit(query)
    source_text = _source_text(query, row)
    constraint = {
        "field": field,
        "operator": operator,
        "value": value,
        "unit": unit,
        "priority": row["default_priority"],
        "source_text": source_text,
    }
    return {
        "case_id": row["phrase_id"],
        "phrase_id": row["phrase_id"],
        "case_type": "operator_phrase",
        "query": query,
        "expected_intent": _expected_intent(query, constraints=[constraint]),
    }


def _soft_marker_examples(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    template_by_id = {
        "OP091": "Shampoo, ideally under 200 baht",
        "OP092": "Shampoo, preferably under 200 baht",
        "OP093": "I prefer shampoo under 200 baht",
        "OP094": "I'd prefer shampoo under 200 baht",
        "OP095": "I would prefer shampoo under 200 baht",
        "OP096": "I would like shampoo under 200 baht",
        "OP097": "I'd like shampoo under 200 baht",
        "OP098": "I want to keep shampoo under 200 baht",
    }
    examples: list[dict[str, Any]] = []
    for row in rows:
        if row["entry_type"] != "soft_marker":
            continue
        query = template_by_id[row["phrase_id"]]
        source_text = "ideally under 200 baht" if row["phrase_id"] == "OP091" else (
            "preferably under 200 baht" if row["phrase_id"] == "OP092" else "under 200 baht"
        )
        preference = {
            "field": "price",
            "preference": _slug(source_text),
            "source_text": source_text,
            "operator": "lte",
            "value": 200,
            "unit": "THB",
        }
        examples.append(
            {
                "case_id": f"{row['phrase_id']}_example",
                "phrase_id": row["phrase_id"],
                "case_type": "soft_marker",
                "query": query,
                "expected_intent": _expected_intent(query, soft_preferences=[preference]),
            }
        )
    return examples


def _regression_examples() -> list[dict[str, Any]]:
    query = "shampoo for dry hair not over\u00a0 200 baht"
    source_text = "not over\u00a0 200 baht"
    return [
        {
            "case_id": "REG_NOT_OVER_NBSP",
            "phrase_id": "OP009",
            "case_type": "intent_regression",
            "query": query,
            "expected_intent": _expected_intent(
                query,
                constraints=[{
                    "field": "price", "operator": "lte", "value": 200, "unit": "THB",
                    "priority": "hard", "source_text": source_text,
                }],
                attributes=[{"name": "hair_type", "value": "dry"}],
            ),
        },
        {
            "case_id": "REG_MULTIPLE_CONSTRAINTS",
            "phrase_id": "OP001|OP018",
            "case_type": "intent_regression",
            "query": "shampoo under 200 baht and at least 4 stars",
            "expected_intent": _expected_intent(
                "shampoo under 200 baht and at least 4 stars",
                constraints=[
                    {"field": "price", "operator": "lte", "value": 200, "unit": "THB", "priority": "hard", "source_text": "under 200 baht"},
                    {"field": "rating", "operator": "gte", "value": 4, "unit": "stars", "priority": "hard", "source_text": "at least 4 stars"},
                ],
            ),
        },
    ]


def build(output_csv: Path = OUTPUT_CSV, output_jsonl: Path = OUTPUT_JSONL) -> dict[str, Any]:
    rows = _read_lexicon()
    numeric_rows = [row for row in rows if row["entry_type"] == "numeric_operator"]
    for row in rows:
        if row["entry_type"] == "numeric_operator" and row["canonical_operator"] not in VALID_OPERATORS:
            raise ValueError(f"Invalid operator {row['canonical_operator']!r} for {row['phrase_id']}")
    examples = [_numeric_example(row) for row in numeric_rows]
    examples.extend(_soft_marker_examples(rows))
    examples.extend(_regression_examples())

    columns = ["case_id", "phrase_id", "case_type", "query", "expected_intent"]
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for example in examples:
            row = dict(example)
            row["expected_intent"] = json.dumps(example["expected_intent"], ensure_ascii=False, separators=(",", ":"))
            writer.writerow(row)
    output_jsonl.write_text(
        "".join(json.dumps(example, ensure_ascii=False, separators=(",", ":")) + "\n" for example in examples),
        encoding="utf-8",
    )
    manifest = {
        "dataset": "operator_phrase_examples_v1",
        "language": "en",
        "lexicon_entries": len(rows),
        "numeric_operator_phrases": len(numeric_rows),
        "soft_preference_markers": sum(row["entry_type"] == "soft_marker" for row in rows),
        "expected_output_examples": len(examples),
        "operators": sorted({row["canonical_operator"] for row in numeric_rows}),
        "data_origin": "curated rule-coverage examples; not real customer queries",
        "lexicon_sha256": hashlib.sha256(LEXICON_PATH.read_bytes()).hexdigest(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--output-jsonl", type=Path, default=OUTPUT_JSONL)
    args = parser.parse_args()
    manifest = build(args.output_csv, args.output_jsonl)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
