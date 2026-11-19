"""Train and evaluate a currency-code classifier on CLDR-derived query data."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.pipeline import Pipeline

try:
    from .validate_currency_dataset import DEFAULT_DATA_DIR, REPO_ROOT, validate
except ImportError:
    from validate_currency_dataset import DEFAULT_DATA_DIR, REPO_ROOT, validate


DEFAULT_PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "currency_resolution" / "v1"
DEFAULT_MODEL_PATH = REPO_ROOT / "experiments" / "models" / "currency_resolution" / "cldr49_currency_classifier.joblib"
DEFAULT_METRICS_PATH = REPO_ROOT / "experiments" / "currency_resolution" / "cldr49_training_metrics.json"


def _split_for_template(template_id: str) -> str:
    match = re.search(r"_(\d\d)$", template_id)
    if not match:
        raise ValueError(f"Unknown query template ID: {template_id}")
    suffix = int(match.group(1))
    if suffix in {1, 2}:
        return "train"
    if suffix == 3:
        return "validation"
    if suffix == 4:
        return "test"
    raise ValueError(f"No split is configured for query template ID: {template_id}")


def _read_examples(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _model() -> Pipeline:
    return Pipeline(
        [
            (
                "features",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(2, 5),
                    min_df=2,
                    max_features=100_000,
                    dtype=np.float32,
                    lowercase=True,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "classifier",
                SGDClassifier(
                    loss="log_loss",
                    alpha=1e-5,
                    max_iter=40,
                    tol=1e-3,
                    class_weight="balanced",
                    random_state=17,
                ),
            ),
        ]
    )


def _evaluate(model: Pipeline, rows: list[dict[str, str]]) -> dict[str, Any]:
    labeled = [row for row in rows if row["training_eligible"] == "true" and row["currency_code"]]
    queries = [row["query"] for row in labeled]
    actual = np.asarray([row["currency_code"] for row in labeled])
    predicted = model.predict(queries)
    probabilities = model.predict_proba(queries)
    labels = list(model.named_steps["classifier"].classes_)
    top_k = min(3, len(labels))
    return {
        "eligible_labeled_rows": len(labeled),
        "ambiguous_rows_excluded": len(rows) - len(labeled),
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(actual, predicted, labels=labels, average="weighted", zero_division=0)),
        "top_3_accuracy": float(top_k_accuracy_score(actual, probabilities, k=top_k, labels=labels)),
        "currency_codes_in_eval": len(set(actual)),
        "rows_per_code_min": min(Counter(actual).values(), default=0),
        "rows_per_code_max": max(Counter(actual).values(), default=0),
    }


def train(
    data_dir: Path = DEFAULT_DATA_DIR,
    processed_dir: Path = DEFAULT_PROCESSED_DIR,
    model_path: Path = DEFAULT_MODEL_PATH,
    metrics_path: Path = DEFAULT_METRICS_PATH,
) -> dict[str, Any]:
    errors, dataset_summary = validate(data_dir)
    if errors:
        raise ValueError("Currency dataset validation failed:\n" + "\n".join(errors[:30]))

    source_rows, source_columns = _read_examples(data_dir / "currency_query_examples.csv")
    rows = [dict(row, split=_split_for_template(row["query_template_id"])) for row in source_rows]
    splits = {
        split: [row for row in rows if row["split"] == split]
        for split in ("train", "validation", "test")
    }
    templates_by_split = {
        split: {row["query_template_id"] for row in split_rows}
        for split, split_rows in splits.items()
    }
    if any(templates_by_split[left] & templates_by_split[right] for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise RuntimeError("Query template leakage detected between train, validation, and test")

    registry_rows, _ = _read_examples(data_dir / "currency_registry.csv")
    currency_codes = {row["currency_code"] for row in registry_rows}
    trainable_train = [
        row for row in splits["train"] if row["training_eligible"] == "true" and row["currency_code"]
    ]
    present_train_codes = {row["currency_code"] for row in trainable_train}
    missing_train_codes = sorted(currency_codes - present_train_codes)
    if missing_train_codes:
        raise RuntimeError(f"No train examples for currency codes: {missing_train_codes}")

    processed_dir.mkdir(parents=True, exist_ok=True)
    columns = source_columns + ["split"]
    for split, split_rows in splits.items():
        split_rows.sort(key=lambda row: (row["query_template_id"], row["example_id"]))
        _write_csv(processed_dir / f"{split}.csv", split_rows, columns)
        _write_jsonl(processed_dir / f"{split}.jsonl", split_rows)

    model = _model()
    model.fit(
        [row["query"] for row in trainable_train],
        [row["currency_code"] for row in trainable_train],
    )
    # Keep the persisted research artifact smaller; sklearn inference supports float32 weights.
    classifier = model.named_steps["classifier"]
    classifier.coef_ = classifier.coef_.astype(np.float32)
    classifier.intercept_ = classifier.intercept_.astype(np.float32)
    validation_metrics = _evaluate(model, splits["validation"])
    test_metrics = _evaluate(model, splits["test"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path, compress=3)
    metrics = {
        "model": "character_tfidf_sgd_log_loss",
        "model_path": str(model_path.relative_to(REPO_ROOT)) if model_path.is_relative_to(REPO_ROOT) else str(model_path),
        "dataset": "CLDR-derived synthetic currency mention queries; not production search logs",
        "cldr_version": json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))["cldr_version"],
        "split_strategy": "query_template_id; suffix 01-02=train, 03=validation, 04=test",
        "ambiguous_alias_policy": "Ambiguous aliases are retained in split datasets for audit and excluded from classifier fitting and scoring.",
        "split_counts": {
            split: {
                "all_rows": len(split_rows),
                "trainable_rows": sum(row["training_eligible"] == "true" and bool(row["currency_code"]) for row in split_rows),
                "ambiguous_rows": sum(row["resolution_status"] == "ambiguous" for row in split_rows),
                "template_ids": sorted(templates_by_split[split]),
            }
            for split, split_rows in splits.items()
        },
        "validation": validation_metrics,
        "test": test_metrics,
        "limitations": [
            "Synthetic examples use a fixed product category and three amount values.",
            "Currency aliases appear in each split under different query templates, so this evaluates template generalization rather than unseen aliases.",
            "Use the alias registry as the authoritative resolver; use the classifier as a learned fallback and evaluate on reviewed real queries before production.",
        ],
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    args = parser.parse_args()
    metrics = train(args.data_dir, args.processed_dir, args.model_path, args.metrics_path)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
