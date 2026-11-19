"""Evaluate exact-span agreement for the rule-based query baseline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .rule_based_baseline import load_lexicon, predict_spans
    from .validate_dataset import REPO_ROOT
except ImportError:  # Support direct execution as a script from the repository root.
    from rule_based_baseline import load_lexicon, predict_spans
    from validate_dataset import REPO_ROOT


DEFAULT_TEST_FILE = REPO_ROOT / "data" / "processed" / "expression_understanding" / "v1" / "test.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "experiments" / "query_understanding_baseline_v1.json"


def _normalise(text: str) -> str:
    return " ".join(text.casefold().split())


def _scores(true_positive: int, predicted: int, gold: int) -> dict[str, float]:
    precision = true_positive / predicted if predicted else 0.0
    recall = true_positive / gold if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate(test_path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in test_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    lexicon = load_lexicon()
    counts: Counter[str] = Counter()
    by_label: dict[str, Counter[str]] = {}
    for record in records:
        gold = {
            (_normalise(annotation["text"]), annotation["label"])
            for annotation in record["expression_annotations"]
        }
        predicted = {
            (_normalise(annotation["text"]), annotation["label"])
            for annotation in predict_spans(record["query"], lexicon)
        }
        true_positives = gold & predicted
        counts.update(
            {
                "gold": len(gold),
                "predicted": len(predicted),
                "true_positive": len(true_positives),
            }
        )
        for label in {label for _, label in gold | predicted}:
            label_counts = by_label.setdefault(label, Counter())
            label_gold = {span for span in gold if span[1] == label}
            label_predicted = {span for span in predicted if span[1] == label}
            label_counts.update(
                {
                    "gold": len(label_gold),
                    "predicted": len(label_predicted),
                    "true_positive": len(label_gold & label_predicted),
                }
            )

    per_label = {
        label: _scores(values["true_positive"], values["predicted"], values["gold"])
        | {"gold": values["gold"], "predicted": values["predicted"], "true_positive": values["true_positive"]}
        for label, values in sorted(by_label.items())
    }
    macro_f1 = sum(scores["f1"] for scores in per_label.values()) / len(per_label) if per_label else 0.0
    return {
        "evaluation": "exact span-and-label match",
        "dataset_status": "constructed seed examples; annotations require human review",
        "test_rows": len(records),
        "gold_spans": counts["gold"],
        "predicted_spans": counts["predicted"],
        "true_positive_spans": counts["true_positive"],
        "micro": _scores(counts["true_positive"], counts["predicted"], counts["gold"]),
        "macro_f1_over_present_labels": macro_f1,
        "per_label": per_label,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-file", type=Path, default=DEFAULT_TEST_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = evaluate(args.test_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Saved: {args.output.relative_to(REPO_ROOT) if args.output.is_relative_to(REPO_ROOT) else args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
