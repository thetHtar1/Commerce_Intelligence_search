"""Create deterministic train/validation/test splits grouped by query template."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from validate_dataset import DEFAULT_DATA_DIR, REPO_ROOT, validate


DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "expression_understanding" / "v1"
SPLIT_RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
PRODUCT_TERMS = sorted(
    {
        "washing machine",
        "cleaning spray",
        "water bottle",
        "office chair",
        "running shoes",
        "hiking backpack",
        "hiking shoes",
        "furniture store",
        "cordless vacuum",
        "noise-cancelling headphones",
        "Bluetooth speaker",
        "portable monitor",
        "smartwatch",
        "headphones",
        "dishwasher",
        "refrigerator",
        "conditioner",
        "shampoo",
        "laptop",
        "chair",
        "desk",
        "sofa",
        "speaker",
        "monitor",
        "printer",
        "bottle",
        "sheets",
        "backpack",
        "bag",
        "jacket",
        "watch",
        "sunglasses",
        "tablet",
        "camera",
        "vacuum",
        "detergent",
        "snacks",
        "phone",
        "pan",
    },
    key=len,
    reverse=True,
)
NUMBER_PATTERN = re.compile(
    r"(?:[$€£฿]\s*\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s*"
    r"(?:baht|thb|usd|stars?|gb|tb|kg|grams?|lb|liters?|liter|hours?|days?|inches?)\b)",
    flags=re.IGNORECASE,
)


def make_template_key(query: str, annotations: list[dict[str, Any]]) -> str:
    """Delexicalize annotated spans, product names, and numeric values."""
    spans: list[tuple[int, int, str]] = []
    for annotation in annotations:
        text = annotation["text"]
        match = re.search(re.escape(text), query, flags=re.IGNORECASE)
        if match:
            role = annotation.get("contextual_role") or "unspecified"
            label = annotation.get("label") or "unlabelled"
            spans.append((match.start(), match.end(), f"<{label}:{role}>"))

    spans.sort(key=lambda span: (span[0], -(span[1] - span[0])))
    pieces: list[str] = []
    cursor = 0
    for start, end, marker in spans:
        if start < cursor:
            continue
        pieces.extend((query[cursor:start], marker))
        cursor = end
    pieces.append(query[cursor:])
    key = "".join(pieces)

    for product_term in PRODUCT_TERMS:
        key = re.sub(
            rf"(?<!\w){re.escape(product_term)}(?!\w)",
            "<product>",
            key,
            flags=re.IGNORECASE,
        )
    key = NUMBER_PATTERN.sub("<number>", key)
    key = re.sub(r"\s+", " ", key.casefold()).strip()
    return key


def _target_counts(total: int, ratios: dict[str, float]) -> dict[str, int]:
    counts = {"train": round(total * ratios["train"]), "validation": round(total * ratios["validation"])}
    counts["test"] = total - counts["train"] - counts["validation"]
    return counts


def assign_groups(
    groups: dict[str, list[dict[str, Any]]],
    seed: int,
) -> dict[str, str]:
    """Greedily balance rows and label coverage without splitting a template group."""
    total_rows = sum(len(group_rows) for group_rows in groups.values())
    row_targets = _target_counts(total_rows, SPLIT_RATIOS)
    labels_by_group = {
        key: {
            annotation["label"]
            for row in rows
            for annotation in row["_annotations"]
        }
        for key, rows in groups.items()
    }
    label_group_totals = Counter(label for labels in labels_by_group.values() for label in labels)
    label_targets = {
        split: {label: label_group_totals[label] * SPLIT_RATIOS[split] for label in label_group_totals}
        for split in SPLIT_RATIOS
    }
    row_counts = Counter()
    label_counts = {split: Counter() for split in SPLIT_RATIOS}

    def stable_hash(value: str) -> str:
        return hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()

    ordered_keys = sorted(
        groups,
        key=lambda key: (
            -sum(1 / label_group_totals[label] for label in labels_by_group[key]),
            -len(groups[key]),
            stable_hash(key),
        ),
    )
    assignments: dict[str, str] = {}
    for key in ordered_keys:
        labels = labels_by_group[key]
        scores: dict[str, float] = {}
        for split in SPLIT_RATIOS:
            row_deficit = (row_targets[split] - row_counts[split]) / max(row_targets[split], 1)
            label_deficit = sum(
                (label_targets[split][label] - label_counts[split][label])
                / max(label_targets[split][label], 0.5)
                for label in labels
            ) / max(len(labels), 1)
            scores[split] = 0.55 * row_deficit + 0.45 * label_deficit
        split = max(SPLIT_RATIOS, key=lambda name: (scores[name], stable_hash(name + key)))
        assignments[key] = split
        row_counts[split] += len(groups[key])
        label_counts[split].update(labels)
    return assignments


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            output = {column: row[column] for column in columns}
            if "expression_annotations" in columns and "_annotations" in row:
                output["expression_annotations"] = json.dumps(
                    row["_annotations"], ensure_ascii=False, separators=(",", ":")
                )
            writer.writerow(output)


def write_splits(data_dir: Path, output_dir: Path, seed: int = 17) -> dict[str, Any]:
    errors, _, _ = validate(data_dir)
    if errors:
        raise ValueError("Dataset validation failed:\n" + "\n".join(errors))

    source_path = data_dir / "contextual_query_examples.csv"
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
        columns = list(source_rows[0].keys())

    rows: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source_row in source_rows:
        row: dict[str, Any] = dict(source_row)
        row["_annotations"] = json.loads(source_row["expression_annotations"])
        row["_template_key"] = make_template_key(row["query"], row["_annotations"])
        rows.append(row)
        groups[row["_template_key"]].append(row)

    assignments = assign_groups(groups, seed)
    rows_by_split = {
        split: sorted(
            (row for row in rows if assignments[row["_template_key"]] == split),
            key=lambda row: row["query_id"],
        )
        for split in SPLIT_RATIOS
    }

    template_splits: dict[str, set[str]] = defaultdict(set)
    for key, split in assignments.items():
        template_splits[hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]].add(split)
    leaking_templates = [template_id for template_id, splits in template_splits.items() if len(splits) > 1]
    if leaking_templates:
        raise RuntimeError(f"Template leakage detected: {leaking_templates}")

    manifest_rows: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "seed": seed,
        "ratios": SPLIT_RATIOS,
        "total_rows": len(rows),
        "unique_template_groups": len(groups),
        "split_counts": {},
        "label_counts": {},
    }
    for split, split_rows in rows_by_split.items():
        _write_csv(output_dir / f"{split}.csv", split_rows, columns)
        jsonl_path = output_dir / f"{split}.jsonl"
        with jsonl_path.open("w", encoding="utf-8", newline="") as handle:
            for row in split_rows:
                output = {column: row[column] for column in columns}
                output["expression_annotations"] = row["_annotations"]
                handle.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n")
        split_label_counts: Counter[str] = Counter(
            annotation["label"] for row in split_rows for annotation in row["_annotations"]
        )
        summary["split_counts"][split] = len(split_rows)
        summary["label_counts"][split] = dict(sorted(split_label_counts.items()))
        for row in split_rows:
            template_id = hashlib.sha256(row["_template_key"].encode("utf-8")).hexdigest()[:12]
            manifest_rows.append(
                {
                    "query_id": row["query_id"],
                    "split": split,
                    "template_id": template_id,
                    "query": row["query"],
                }
            )

    _write_csv(
        output_dir / "split_manifest.csv",
        manifest_rows,
        ["query_id", "split", "template_id", "query"],
    )
    summary["template_leakage"] = 0
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "split_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    summary = write_splits(args.data_dir, args.output_dir, args.seed)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
