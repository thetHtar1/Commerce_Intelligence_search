# Data architecture

## Dataset lifecycle

- `data/raw/`: immutable source exports.
- `data/interim/`: cleaned or joined intermediate data.
- `data/processed/`: model- and evaluation-ready datasets.
- `data/synthetic/`: generated examples, clearly identified as synthetic.
- `data/labels/`: relevance judgments and annotation metadata.

Document schemas, provenance, refresh cadence, privacy constraints, and validation rules for each dataset.
