"""Validate the seed expression lexicon and annotated query dataset."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "training" / "expression_understanding"
LABELS = {
    "hard_constraint",
    "soft_preference",
    "product_attribute",
    "negation",
    "comparison",
    "ambiguous_expression",
}
CONFIDENCE_VALUES = {"high", "medium", "low"}
OPERATORS = {"<", "<=", ">", ">=", "=", "between", "required", "exclude", "near"}
LEXICON_COLUMNS = {
    "expression",
    "expression_family",
    "typical_role",
    "target_attribute",
    "contextual_interpretation",
}
QUERY_COLUMNS = {
    "query_id",
    "query",
    "domain",
    "expression_annotations",
    "data_origin",
    "annotation_status",
}
ANNOTATION_FIELDS = {
    "text",
    "label",
    "attribute",
    "operator",
    "value",
    "unit",
    "contextual_role",
    "confidence",
}


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def _span_position(query: str, text: str) -> tuple[int, int] | None:
    match = re.search(re.escape(text), query, flags=re.IGNORECASE)
    return (match.start(), match.end()) if match else None


def validate(data_dir: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    lexicon_path = data_dir / "expression_lexicon.csv"
    csv_path = data_dir / "contextual_query_examples.csv"
    jsonl_path = data_dir / "contextual_query_examples.jsonl"
    for path in (lexicon_path, csv_path, jsonl_path):
        if not path.is_file():
            errors.append(f"Missing required file: {path}")
    if errors:
        return errors, warnings, {}

    lexicon_rows, lexicon_columns = _read_csv(lexicon_path)
    query_rows, query_columns = _read_csv(csv_path)
    for column in sorted(LEXICON_COLUMNS - set(lexicon_columns)):
        errors.append(f"expression_lexicon.csv is missing column {column!r}")
    for column in sorted(QUERY_COLUMNS - set(query_columns)):
        errors.append(f"contextual_query_examples.csv is missing column {column!r}")

    lexicon_duplicates: dict[str, list[int]] = defaultdict(list)
    lexicon_family_counts: Counter[str] = Counter()
    for row_number, row in enumerate(lexicon_rows, start=2):
        expression = (row.get("expression") or "").strip()
        if not expression:
            errors.append(f"expression_lexicon.csv row {row_number}: empty expression")
            continue
        lexicon_duplicates[_normalise(expression)].append(row_number)
        family = (row.get("expression_family") or "").strip()
        lexicon_family_counts[family] += 1
        if family not in LABELS:
            errors.append(f"expression_lexicon.csv row {row_number}: invalid family {family!r}")
        for column in LEXICON_COLUMNS - {"expression_family"}:
            if not (row.get(column) or "").strip():
                errors.append(f"expression_lexicon.csv row {row_number}: missing {column}")
    for expression, row_numbers in lexicon_duplicates.items():
        if len(row_numbers) > 1:
            errors.append(
                f"Duplicate lexicon expression {expression!r} on rows {row_numbers}"
            )

    ids: dict[str, list[int]] = defaultdict(list)
    query_texts: dict[str, list[str]] = defaultdict(list)
    label_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    annotation_count = 0
    empty_summaries = 0
    parsed_by_id: dict[str, list[dict[str, Any]]] = {}
    row_by_id: dict[str, dict[str, str]] = {}
    span_overlap_count = 0

    for row_number, row in enumerate(query_rows, start=2):
        query_id = (row.get("query_id") or "").strip()
        query = (row.get("query") or "").strip()
        for field in ("domain", "data_origin", "annotation_status"):
            if not (row.get(field) or "").strip():
                errors.append(f"contextual_query_examples.csv row {row_number}: missing {field}")
        if not query_id:
            errors.append(f"contextual_query_examples.csv row {row_number}: missing query_id")
        if not query:
            errors.append(f"contextual_query_examples.csv row {row_number}: missing query")
        ids[query_id].append(row_number)
        query_texts[_normalise(query)].append(query_id)
        row_by_id[query_id] = row
        status_counts[(row.get("annotation_status") or "").strip()] += 1
        if not (row.get("intent_summary") or "").strip():
            empty_summaries += 1

        raw_annotations = row.get("expression_annotations") or ""
        try:
            annotations = json.loads(raw_annotations)
        except json.JSONDecodeError as exc:
            errors.append(f"{query_id}: invalid expression_annotations JSON: {exc.msg}")
            continue
        if not isinstance(annotations, list):
            errors.append(f"{query_id}: expression_annotations must be an array")
            continue
        parsed_by_id[query_id] = annotations
        if not annotations:
            errors.append(f"{query_id}: no expression annotations")

        spans: list[tuple[int, int, str]] = []
        for annotation_index, annotation in enumerate(annotations, start=1):
            annotation_count += 1
            prefix = f"{query_id} annotation {annotation_index}"
            if not isinstance(annotation, dict):
                errors.append(f"{prefix}: annotation must be an object")
                continue
            for field in sorted(ANNOTATION_FIELDS - annotation.keys()):
                errors.append(f"{prefix}: missing field {field!r}")
            text = annotation.get("text")
            label = annotation.get("label")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{prefix}: text must be a non-empty string")
                continue
            if label not in LABELS:
                errors.append(f"{prefix}: invalid label {label!r}")
            else:
                label_counts[label] += 1
            for field in ("attribute", "contextual_role"):
                field_value = annotation.get(field)
                if field_value is not None and (not isinstance(field_value, str) or not field_value.strip()):
                    errors.append(f"{prefix}: {field} must be a non-empty string or null")
            if annotation.get("confidence") not in CONFIDENCE_VALUES:
                errors.append(f"{prefix}: invalid confidence {annotation.get('confidence')!r}")
            operator = annotation.get("operator")
            if operator is not None and operator not in OPERATORS:
                errors.append(f"{prefix}: invalid operator {operator!r}")
            value = annotation.get("value")
            if value is not None and not isinstance(value, (str, int, float, dict)):
                errors.append(f"{prefix}: value must be a string, number, range object, or null")
            if label == "hard_constraint" and (operator is None or value is None):
                errors.append(f"{prefix}: hard constraint requires operator and value")
            if label == "negation" and (operator != "exclude" or value is None):
                errors.append(f"{prefix}: negation requires exclude operator and target value")
            if label in {"hard_constraint", "soft_preference"} and re.search(r"\d|[$฿]", text):
                if operator is None or value is None:
                    errors.append(f"{prefix}: explicit numeric preference/constraint lacks operator or value")
                if re.search(r"[$฿]|\b(?:baht|thb|usd|stars?|gb|tb|kg|grams?|lb|liters?|liter|hours?|days?|inches?|reviews?)\b", text, re.I) and not annotation.get("unit"):
                    errors.append(f"{prefix}: explicit numeric preference/constraint lacks its unit")
            if operator == "between" and not (
                isinstance(value, dict) and {"min", "max"}.issubset(value)
            ):
                errors.append(f"{prefix}: between operator requires a value object with min and max")

            position = _span_position(query, text)
            if position is None:
                errors.append(f"{prefix}: span {text!r} does not occur in the query")
            else:
                spans.append((*position, text))

        spans.sort()
        for previous, current in zip(spans, spans[1:]):
            if current[0] < previous[1]:
                span_overlap_count += 1
                errors.append(
                    f"{query_id}: overlapping annotation spans {previous[2]!r} and {current[2]!r}"
                )

    for query_id, row_numbers in ids.items():
        if query_id and len(row_numbers) > 1:
            errors.append(f"Duplicate query_id {query_id!r} on rows {row_numbers}")
    for normalized_query, query_ids in query_texts.items():
        if normalized_query and len(query_ids) > 1:
            errors.append(f"Duplicate query text on query_ids {query_ids}")

    jsonl_rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(jsonl_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            errors.append(f"contextual_query_examples.jsonl line {line_number}: blank line")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"contextual_query_examples.jsonl line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"contextual_query_examples.jsonl line {line_number}: row must be an object")
            continue
        if not isinstance(record.get("expression_annotations"), list):
            errors.append(
                f"contextual_query_examples.jsonl line {line_number}: expression_annotations must be a native array"
            )
        jsonl_rows.append(record)

    if len(jsonl_rows) != len(query_rows):
        errors.append(
            f"CSV/JSONL row count mismatch: {len(query_rows)} CSV rows and {len(jsonl_rows)} JSONL rows"
        )
    else:
        for row_number, (csv_row, jsonl_row) in enumerate(zip(query_rows, jsonl_rows), start=2):
            query_id = csv_row.get("query_id", f"row {row_number}")
            expected = dict(csv_row)
            try:
                expected["expression_annotations"] = json.loads(expected["expression_annotations"])
            except (KeyError, json.JSONDecodeError):
                continue
            if expected != jsonl_row:
                errors.append(f"CSV/JSONL content mismatch for {query_id}")

    if query_rows and all(status == "requires_human_review" for status in status_counts):
        warnings.append(
            f"All {len(query_rows)} examples still require human review; do not treat labels as gold"
        )
    if empty_summaries:
        warnings.append(
            f"{empty_summaries} intent_summary fields are empty; they are optional and unused in this split"
        )

    summary = {
        "lexicon_rows": len(lexicon_rows),
        "query_rows": len(query_rows),
        "annotation_rows": annotation_count,
        "label_counts": dict(sorted(label_counts.items())),
        "lexicon_family_counts": dict(sorted(lexicon_family_counts.items())),
        "annotation_status_counts": dict(sorted(status_counts.items())),
        "empty_intent_summaries": empty_summaries,
        "annotation_span_overlaps": span_overlap_count,
        "jsonl_rows": len(jsonl_rows),
    }
    return errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    errors, warnings, summary = validate(args.data_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Validation: {'PASS' if not errors else 'FAIL'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
