"""Validate the CLDR currency registry, aliases, and synthetic query examples."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "training" / "currency_resolution"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(data_dir: Path = DEFAULT_DATA_DIR) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    paths = {
        "registry": data_dir / "currency_registry.csv",
        "aliases": data_dir / "currency_aliases.csv",
        "examples": data_dir / "currency_query_examples.csv",
        "jsonl": data_dir / "currency_query_examples.jsonl",
        "manifest": data_dir / "dataset_manifest.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        return [f"Missing required file: {path}" for path in missing], {}

    registry = _read_csv(paths["registry"])
    aliases = _read_csv(paths["aliases"])
    examples = _read_csv(paths["examples"])
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))

    codes = [row["currency_code"] for row in registry]
    code_set = set(codes)
    duplicate_codes = [code for code, count in Counter(codes).items() if count > 1]
    if duplicate_codes:
        errors.append(f"Duplicate currency codes: {duplicate_codes[:10]}")
    invalid_codes = [code for code in codes if not re.fullmatch(r"[A-Z]{3}", code)]
    if invalid_codes:
        errors.append(f"Invalid ISO-style currency codes: {invalid_codes[:10]}")
    missing_names = [row["currency_code"] for row in registry if not row["en_display_name"]]
    if missing_names:
        errors.append(f"Missing English display names: {missing_names[:10]}")

    alias_ids = [row["alias_id"] for row in aliases]
    if len(alias_ids) != len(set(alias_ids)):
        errors.append("Duplicate alias_id values")
    alias_normalized = [row["normalized_alias"] for row in aliases]
    if len(alias_normalized) != len(set(alias_normalized)):
        errors.append("Duplicate normalized aliases")
    for row in aliases:
        candidates = [code for code in row["candidate_codes"].split("|") if code]
        if not candidates or not set(candidates).issubset(code_set):
            errors.append(f"Alias {row['alias']!r} points to missing currency code(s): {candidates}")
        expected_status = "unique" if len(candidates) == 1 else "ambiguous"
        if row["resolution_status"] != expected_status:
            errors.append(f"Alias {row['alias']!r} has an inconsistent resolution_status")
        if (row["training_eligible"] == "true") != (expected_status == "unique"):
            errors.append(f"Alias {row['alias']!r} has inconsistent training eligibility")

    ids = [row["example_id"] for row in examples]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate query example IDs")
    for row in examples:
        if not row["query"].strip():
            errors.append(f"Example {row['example_id']} has an empty query")
        candidates = [code for code in row["candidate_codes"].split("|") if code]
        if not set(candidates).issubset(code_set):
            errors.append(f"Example {row['example_id']} refers to a code missing from the registry")
        if row["resolution_status"] == "unique":
            if len(candidates) != 1 or row["currency_code"] != candidates[0]:
                errors.append(f"Example {row['example_id']} has an inconsistent unique currency label")
        elif row["currency_code"]:
            errors.append(f"Ambiguous example {row['example_id']} must not have a training label")
        if row["training_eligible"] == "true" and row["resolution_status"] != "unique":
            errors.append(f"Ambiguous example {row['example_id']} is marked trainable")

    jsonl_rows = []
    for line_number, line in enumerate(paths["jsonl"].read_text(encoding="utf-8").splitlines(), start=1):
        try:
            jsonl_rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"JSONL line {line_number} is invalid JSON: {exc.msg}")
    if len(jsonl_rows) != len(examples):
        errors.append(f"CSV/JSONL row count mismatch: {len(examples)} != {len(jsonl_rows)}")
    else:
        for index, (csv_row, json_row) in enumerate(zip(examples, jsonl_rows), start=1):
            if any(str(json_row.get(key, "")) != value for key, value in csv_row.items()):
                errors.append(f"CSV/JSONL row {index} differs")
                break

    for code in code_set:
        if not any(row["normalized_alias"] == code.casefold() and code in row["candidate_codes"].split("|") for row in aliases):
            errors.append(f"Currency code {code} has no ISO-code alias")
        if not any(row["currency_code"] == code and row["training_eligible"] == "true" for row in examples):
            errors.append(f"Currency code {code} has no trainable query example")

    if manifest.get("currencies") != len(registry):
        errors.append("Manifest currency count does not match currency registry")
    if manifest.get("aliases") != len(aliases):
        errors.append("Manifest alias count does not match currency alias file")
    if manifest.get("query_examples") != len(examples):
        errors.append("Manifest example count does not match query dataset")

    summary = {
        "currencies": len(registry),
        "current_tender": sum(row["currency_status"] == "current_tender" for row in registry),
        "historical_or_non_tender": sum(row["currency_status"] != "current_tender" for row in registry),
        "aliases": len(aliases),
        "ambiguous_aliases": sum(row["resolution_status"] == "ambiguous" for row in aliases),
        "query_examples": len(examples),
        "trainable_examples": sum(row["training_eligible"] == "true" for row in examples),
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    errors, summary = validate(args.data_dir)
    print(json.dumps({"valid": not errors, "summary": summary, "errors": errors}, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
