# Commerce_Intelligence_search

AI-native e-commerce search and research platform combining LLM-based intent understanding, semantic retrieval, ML ranking, product comparison, recommendation, and adaptive shopping experiences.

An AI-native e-commerce search system that helps shoppers research, compare, and discover products without leaving the e-commerce platform.

## Problem

Online shoppers often switch between e-commerce platforms and general-purpose AI assistants when researching products. This project aims to integrate AI-powered product research directly into the e-commerce search experience.

## Core capabilities

- Natural-language shopping search
- LLM-based query understanding
- Semantic product retrieval
- ML-based product ranking
- Product comparison
- AI shopping assistant
- Research memory
- Dynamic shopping experience
- E-commerce analytics

## Technical focus

- Data Engineering
- Data Science
- Machine Learning
- LLM / AI Agents
- Information Retrieval
- Recommendation Systems
- MLOps

## Repository status

This repository currently contains a research and engineering scaffold. Retrieval and ranking modules mark the intended implementation points; no product dataset or trained model is included yet.

## Repository layout

- `data/` — raw, intermediate, processed, synthetic, and labeled datasets.
- `notebooks/` — numbered exploration, preprocessing, query analysis, and evaluation notebooks.
- `src/` — reusable code for data, features, query understanding, retrieval, ranking, evaluation, pipelines, and monitoring.
- `warehouse/` — SQL transformations and dbt assets.
- `api/` and `frontend/` — planned search service and interface.
- `configs/`, `experiments/`, and `tests/` — configuration, experiment outputs, and tests.
- `docs/` — problem definition, architecture, retrieval, ranking, and evaluation plans.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Add source catalog data under `data/raw/`. Keep derived data under `data/interim/` and `data/processed/`, and record relevance judgments under `data/labels/`.

Currency reference data and the query-resolution training workflow are documented in [`docs/currency_data_and_training.md`](docs/currency_data_and_training.md). The CLDR-derived currency dataset is stored under `data/training/currency_resolution/`.
