# Currency Data and Training Process

## Scope

Currency reference data is sourced from Unicode CLDR JSON 49.0.0. The stored snapshots cover CLDR's currency codes and locale display data for English, Burmese (`my`), and Thai (`th`). The generated registry currently contains 306 codes: 153 marked as current tender in at least one region and 153 marked historical or non-tender. Keep both groups so historical mentions can be recognized without presenting them as currently used tender.

## Data flow

```text
data/raw/currency/ (CLDR snapshots + license)
        ↓ build_currency_dataset.py
data/training/currency_resolution/ (registry + aliases + synthetic queries)
        ↓ validate_currency_dataset.py
        ↓ train_currency_model.py
data/processed/currency_resolution/v1/ (template-grouped splits)
experiments/models/currency_resolution/ (trained classifier)
experiments/currency_resolution/ (metrics)
```

The builder stores names, singular/plural forms, symbols, alternate/narrow symbols, ISO codes, English core currency-unit names, localized names, active tender regions, and minor-unit digits. Alias collisions are preserved as candidate-code lists. A currency alias is trainable only when it points to one code.

## Reproducible commands

```bash
python src/query_understanding/build_currency_dataset.py
python src/query_understanding/validate_currency_dataset.py
python src/query_understanding/train_currency_model.py
python src/query_understanding/predict_currency.py "Find shampoo under 200 Thai baht"
```

Training uses character TF-IDF features and an SGD logistic classifier. Query templates are grouped by `query_template_id`: template suffixes `_01` and `_02` are train, `_03` is validation, and `_04` is test. Ambiguous labels remain in the partitioned dataset for review but do not enter classifier fit or score calculations.

The rule-based intent baseline loads the alias registry rather than maintaining a short currency list. It writes the ISO code into the price constraint's `unit` when the query identifies one currency. If a generic symbol such as `$` has multiple candidate codes and no explicit code/name resolves it, the baseline keeps the candidate list in `ambiguities` and sets `needs_clarification`.

## Evaluation limits

The test set holds out query wording templates while retaining the same aliases across splits. This checks template generalization, not unseen-currency aliases. The examples are synthetic, use shampoo and a few fixed amounts, and must not be treated as customer search data. The current metrics are development indicators only; evaluate against human-reviewed, real query examples before production.

## Source and license

See [`data/raw/currency/README.md`](../data/raw/currency/README.md) and the license snapshot at [`data/raw/currency/CLDR_LICENSE.txt`](../data/raw/currency/CLDR_LICENSE.txt). Upstream source: [CLDR JSON 49.0.0](https://github.com/unicode-org/cldr-json/tree/49.0.0).
