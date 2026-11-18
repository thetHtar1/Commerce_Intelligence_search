# E-commerce Query Expression Dataset — Seed v1

## Files
- `expression_lexicon.csv`: candidate expression vocabulary and typical contextual meanings.
- `contextual_query_examples.csv`: constructed queries with span-level JSON annotations.
- `contextual_query_examples.jsonl`: same query examples in JSON Lines format.
- `label_guide.md`: annotation definitions and guidance.

## Intended use
This is a starter dataset for contextual query expression classification and extraction in e-commerce search. It complements Amazon ESCI and Wayfair WANDS; it does not replace their query-product relevance judgments.

## Data provenance
All query examples are constructed seed examples, not real customer search logs. The vocabulary is a curated starting list, not exhaustive. All annotations require human review before being treated as gold-standard labels.

## Labels
- `hard_constraint`: mandatory condition or explicit bound.
- `soft_preference`: ranking preference without a strict threshold.
- `product_attribute`: product property/specification; hard/soft status may remain unresolved.
- `negation`: explicit exclusion or absence requirement.
- `comparison`: relative comparison, similarity or substitute intent.
- `ambiguous_expression`: underspecified or context-dependent meaning.

## Critical annotation rules
1. Label expression spans in context, not isolated tokens.
2. `lightweight laptop` is an attribute; `I prefer a lightweight laptop` is a soft preference; `must be lightweight` is a hard requirement.
3. `under $500` is usually a hard cap; `I prefer laptops under $500` is a preferred cap.
4. Subjective terms such as `affordable`, `good`, `best`, and `reasonable` do not imply numeric thresholds.
5. Numeric operators need target, value and unit. Do not label `at least` without its target/value context.
6. Negation scope matters. `non-stick pan` is a positive product attribute, not a query-level exclusion.
7. Do not infer missing requirements, budgets, units, certifications or product properties.
8. Use confidence/ambiguity rather than forcing uncertain labels.

## Suggested experiments
- Rule-based baseline for numeric operators and common phrase patterns.
- Span classification (BIO tagging) for expression detection.
- Multi-task classification for expression family + target attribute.
- Slot extraction for operator, value, unit and comparison target.
- Evaluate span precision/recall/F1, label macro-F1, numeric slot exact match and constraint parsing accuracy.
- Split by templates or expression families to reduce template leakage.

## Limitations
English only; constructed examples; uneven domain coverage; provisional labels; not representative of real customer traffic.
