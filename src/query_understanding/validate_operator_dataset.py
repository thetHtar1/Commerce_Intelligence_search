"""Run the curated operator phrase cases against the query-intent baseline."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

try:
    from .build_operator_dataset import DATA_DIR, LEXICON_PATH
    from .rule_based_baseline import predict_intent
except ImportError:
    from build_operator_dataset import DATA_DIR, LEXICON_PATH
    from rule_based_baseline import predict_intent


DEFAULT_EXAMPLES = DATA_DIR / "operator_phrase_examples.csv"
VALID_OPERATORS = {"lt", "lte", "gt", "gte", "eq", "between", "near"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(examples_path: Path = DEFAULT_EXAMPLES) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not LEXICON_PATH.is_file():
        return [f"Missing operator phrase lexicon: {LEXICON_PATH}"], {}
    if not examples_path.is_file():
        return [f"Missing operator phrase examples: {examples_path}"], {}

    lexicon = _read_csv(LEXICON_PATH)
    examples = _read_csv(examples_path)
    phrase_keys: dict[tuple[str, str], str] = {}
    ids: set[str] = set()
    for row in lexicon:
        if not row.get("phrase_id") or not row.get("phrase"):
            errors.append(f"Lexicon row is missing phrase_id or phrase: {row}")
        if row.get("entry_type") == "numeric_operator":
            operator = row.get("canonical_operator")
            if operator not in VALID_OPERATORS:
                errors.append(f"{row['phrase_id']}: invalid canonical_operator {operator!r}")
            key = (" ".join(row["phrase"].casefold().split()), row["position"])
            if key in phrase_keys and phrase_keys[key] != operator:
                errors.append(f"Conflicting operator mapping for {key}: {phrase_keys[key]} vs {operator}")
            phrase_keys[key] = operator
        if row.get("entry_type") == "soft_marker" and row.get("canonical_operator"):
            errors.append(f"{row['phrase_id']}: soft marker must not map to a numeric operator")

    matched_phrase_ids: set[str] = set()
    for row in examples:
        case_id = row.get("case_id", "")
        if case_id in ids:
            errors.append(f"Duplicate case_id: {case_id}")
        ids.add(case_id)
        try:
            expected = json.loads(row["expected_intent"])
        except (KeyError, json.JSONDecodeError) as exc:
            errors.append(f"{case_id}: expected_intent is not valid JSON ({exc})")
            continue
        actual = predict_intent(row["query"])
        matched_phrase_ids.add(row.get("phrase_id", ""))
        if actual != expected:
            errors.append(
                f"{case_id}: prediction mismatch\n"
                f"  query: {row['query']!r}\n"
                f"  expected: {json.dumps(expected, ensure_ascii=False, sort_keys=True)}\n"
                f"  actual:   {json.dumps(actual, ensure_ascii=False, sort_keys=True)}"
            )

    required_numeric = {row["phrase_id"] for row in lexicon if row.get("entry_type") == "numeric_operator"}
    missing_cases = sorted(required_numeric - matched_phrase_ids)
    if missing_cases:
        errors.append(f"Numeric phrase(s) missing expected-output examples: {missing_cases}")

    summary = {
        "lexicon_entries": len(lexicon),
        "numeric_operator_phrases": len(required_numeric),
        "soft_preference_markers": sum(row.get("entry_type") == "soft_marker" for row in lexicon),
        "expected_output_cases": len(examples),
        "matched_cases": len(examples) - len(errors),
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES)
    args = parser.parse_args()
    errors, summary = validate(args.examples)
    print(json.dumps({"valid": not errors, "summary": summary, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
