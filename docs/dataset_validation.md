# Query Expression Dataset Validation

## Scope

Validation covers the seed dataset in `data/training/expression_understanding/`:

- 164 lexicon entries
- 98 constructed query examples
- 175 span annotations
- 98 JSONL records

Run the repeatable checks from the repository root:

```sh
python src/query_understanding/validate_dataset.py
```

## Validation result

The dataset passes structural and annotation validation after the corrections below.

| Check | Result |
|---|---:|
| Duplicate lexicon expressions | 0 |
| Duplicate query IDs or normalized query texts | 0 |
| Missing/invalid labels or confidence values | 0 |
| Annotation spans absent from their query | 0 |
| Overlapping annotation spans | 0 |
| CSV/JSONL record or annotation mismatches | 0 |
| Missing required constraint, soft-numeric, or exclusion slots | 0 |

### Corrections made

- Converted `expression_annotations` in JSONL from a JSON-encoded string to a native JSON array. The CSV representation remains a JSON string, as required by CSV.
- Added the missing categorical values for `must be lightweight`, `must have Bluetooth`, and `need a compact camera` (Q014, Q088, Q090).
- Filled the numeric operator, value, and unit for the soft price/rating preferences in Q090–Q093.
- Added the explicitly excluded target values for all 11 negation annotations.

The normalized annotation label counts are:

| Label | Spans |
|---|---:|
| `hard_constraint` | 57 |
| `soft_preference` | 37 |
| `product_attribute` | 41 |
| `negation` | 11 |
| `comparison` | 5 |
| `ambiguous_expression` | 24 |

## Review warnings

- All 98 rows are still marked `requires_human_review`. The annotations are seed labels, not gold labels, and should not be used to claim production-quality model performance.
- All 98 `intent_summary` fields are empty. They are optional in the current pipeline and are not used by the split or baseline.
- The examples are constructed English queries, not real customer search logs. Domain coverage and label frequencies are not representative of production traffic.

## Template-grouped splits

`python src/query_understanding/split_dataset.py` creates the artifacts under `data/processed/expression_understanding/v1/`.

| Split | Rows |
|---|---:|
| Train | 67 |
| Validation | 16 |
| Test | 15 |

The requested 70/15/15 target is approximate because complete template groups are kept together. The split uses seed `17`, identifies 92 delexicalized template groups, and verifies zero template groups occur in more than one split. See `split_manifest.csv` and `split_summary.json` in the processed-data directory for the row assignments and label counts.

Because the labels remain unreviewed, these files are provisional development partitions. Rebuild the split after label review or material dataset changes.

## Rule-based baseline

The rule-based reference implementation and its exact-span results are documented in [`experiments/query_understanding_baseline_v1.md`](../experiments/query_understanding_baseline_v1.md). The baseline is a lexicon-plus-pattern prototype, not a trained model.
