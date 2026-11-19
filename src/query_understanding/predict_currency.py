"""Print top currency-code candidates from the trained query classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = REPO_ROOT / "experiments" / "models" / "currency_resolution" / "cldr49_currency_classifier.joblib"


def predict(query: str, model_path: Path = DEFAULT_MODEL_PATH, top_k: int = 3) -> list[dict[str, Any]]:
    if not model_path.is_file():
        raise FileNotFoundError(f"Trained model not found: {model_path}. Run train_currency_model.py first.")
    model = joblib.load(model_path)
    probabilities = model.predict_proba([query])[0]
    classes = model.named_steps["classifier"].classes_
    order = probabilities.argsort()[::-1][:max(1, min(top_k, len(classes)))]
    return [
        {"currency_code": str(classes[index]), "score": float(probabilities[index])}
        for index in order
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Shopping query containing a currency mention")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(predict(args.query, args.model_path, args.top_k), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
