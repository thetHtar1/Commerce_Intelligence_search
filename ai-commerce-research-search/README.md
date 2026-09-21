# ai-commerce-research-search

Research workspace for AI-powered commerce search, ranking, and recommendation.

## Structure

```
ai-commerce-research-search/
├── README.md
├── data/
│   ├── raw/           # immutable source data
│   ├── processed/     # cleaned, analysis-ready data
│   └── synthetic/     # generated / simulated data
├── notebooks/         # exploratory analysis
├── src/
│   ├── data/          # ingestion + loaders
│   ├── features/      # feature engineering
│   ├── search/        # retrieval (lexical, vector, hybrid)
│   ├── ranking/       # learning-to-rank / rerankers
│   ├── recommendation/# recsys models
│   ├── llm/           # prompts, agents, LLM services
│   └── evaluation/    # offline metrics, A/B analysis
├── warehouse/
│   ├── sql/           # ad-hoc + reporting SQL
│   └── dbt/           # dbt project
├── api/               # serving layer
├── frontend/          # demo UI
├── tests/
├── docs/
└── configs/           # config files per environment/experiment
```

## Getting started

```bash
git clone <repo-url>
cd ai-commerce-research-search
```

## Conventions

- Anything in `data/raw/` is read-only; derive everything else.
- Data files are gitignored by default — commit only small samples or schemas.
- Experiment configs live in `configs/`, not hardcoded in `src/`.
