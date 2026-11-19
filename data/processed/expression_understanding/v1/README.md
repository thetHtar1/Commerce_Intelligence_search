# Query Expression Splits — V1

Generated from `data/training/expression_understanding/contextual_query_examples.csv` by `src/query_understanding/split_dataset.py`.

- Seed: `17`
- Target ratios: train `70%`, validation `15%`, test `15%`
- Actual row counts: train `67`, validation `16`, test `15`
- Template groups: `92`
- Template leakage: `0`

Annotated spans are stored as JSON strings in the CSV files and as native arrays in the JSONL files. `split_manifest.csv` maps every `query_id` to a split and stable `template_id`; `split_summary.json` records label counts.

The template key replaces annotated expressions with their label/context role, product category terms with a common token, and numeric literals with a common token. The deterministic group assignment uses seed `17` and balances split size and label coverage. Full groups always stay in one partition.

All source rows are constructed examples marked `requires_human_review`. Treat these splits and their metrics as provisional until human review and adjudication are complete.
