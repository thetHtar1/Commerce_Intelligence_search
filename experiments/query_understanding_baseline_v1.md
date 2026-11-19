# Query Understanding Rule-Based Baseline — V1

## Baseline

`src/query_understanding/rule_based_baseline.py` provides a transparent first-pass parser built from the curated expression lexicon and deterministic patterns for numeric bounds, required attributes, exclusions, comparisons, and contextual expressions. It returns span predictions and projects them into the agreed V1 intent object.

The canonical example `shampoo for dry hair under 200 baht` produces a `hair_type: dry` attribute and a hard `price lte 200 THB` constraint.

Run the baseline evaluation from the repository root:

```sh
python src/query_understanding/evaluate_baseline.py
```

## Initial held-out result

Evaluation uses exact span-and-label match on the template-grouped test split: 15 queries and 28 annotated spans.

| Metric | Score |
|---|---:|
| Micro precision | 0.885 |
| Micro recall | 0.821 |
| Micro F1 | 0.852 |
| Macro F1 over labels present in test | 0.837 |

| Label | Gold spans | Predicted spans | F1 |
|---|---:|---:|---:|
| `hard_constraint` | 9 | 9 | 0.889 |
| `soft_preference` | 6 | 6 | 1.000 |
| `product_attribute` | 6 | 6 | 0.667 |
| `negation` | 2 | 2 | 1.000 |
| `comparison` | 2 | 1 | 0.667 |
| `ambiguous_expression` | 3 | 2 | 0.800 |

Machine-readable counts and metrics are in [`query_understanding_baseline_v1.json`](query_understanding_baseline_v1.json).

## Limits

- The evaluation labels are constructed seed annotations and all remain `requires_human_review`; these scores measure agreement with provisional labels, not gold-standard performance.
- The hand-authored lexicon contains expressions represented in the seed dataset. Template grouping prevents identical delexicalized templates from crossing splits, but does not remove all lexical overlap between the lexicon and the test queries.
- The test set has only 15 queries. Keep this result as a starting reference. Review and adjudicate labels, then freeze a new test set before comparing against an ML model.
- The parser is English-focused and uses a limited product-category list. It is not production-ready and does not cover all query forms or catalog attributes.
