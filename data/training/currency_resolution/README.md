# Currency Resolution Dataset

## Dataset contents

- `currency_registry.csv`: all 306 CLDR 49 currency codes, English names and symbols, Burmese and Thai display names when CLDR supplies them, current tender regions, historical/non-tender status, and minor-unit metadata.
- `currency_aliases.csv`: normalized currency names, codes, symbols, and common English currency-unit forms. Each alias includes its candidate ISO codes. Shared symbols and words such as `$` or `dollars` remain marked ambiguous.
- `currency_query_examples.csv` and `.jsonl`: synthetic shopping queries covering supported aliases, amount formats, and English, Burmese, and Thai query templates. Ambiguous aliases are included with no forced target code.
- `dataset_manifest.json`: CLDR version, row counts, and SHA-256 checksums for every raw source snapshot.

Current tender status is derived from CLDR's region currency data. Historical codes and non-tender codes remain in the registry so the model can recognize them without treating them as current currencies.

## Rebuild and validate

From the repository root:

```bash
python src/query_understanding/build_currency_dataset.py
python src/query_understanding/validate_currency_dataset.py
```

## Train and evaluate

```bash
python src/query_understanding/train_currency_model.py
python src/query_understanding/predict_currency.py "Find shampoo under 200 Thai baht"
```

The script writes template-grouped train/validation/test CSV and JSONL files under `data/processed/currency_resolution/v1/`, a character TF-IDF + SGD classifier under `experiments/models/currency_resolution/`, and evaluation metrics under `experiments/currency_resolution/`.

Template IDs ending in `_01` and `_02` go to train, `_03` to validation, and `_04` to test. The same template ID is never present in more than one split. Ambiguous aliases stay in the split files for auditing and are excluded from model fitting and scoring.

## Limitations

Query examples are synthetic and use a small set of product/amount templates; the classifier's strong held-out template scores do not establish performance on real customer traffic or unseen aliases. The alias table is the deterministic source of truth. Ambiguous currency symbols need an explicit code, currency name, or locale context before a price filter is applied. Review real queries and labels before production use.

## Provenance and license

Raw currency names, symbols, tender regions, and fraction digits come from Unicode CLDR JSON 49.0.0. The source files and copied license are in [`../../raw/currency/`](../../raw/currency/). See the [CLDR JSON release](https://github.com/unicode-org/cldr-json/tree/49.0.0) and its [license](https://github.com/unicode-org/cldr-json/blob/49.0.0/LICENSE).
