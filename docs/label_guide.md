# Query Expression Label Guide — V1

This guide defines the span labels used by `contextual_query_examples.csv` and `contextual_query_examples.jsonl`. The labels describe each expression in its query context; they do not claim to be verified product facts.

## Label definitions

| Label | Apply when | Examples |
|---|---|---|
| `hard_constraint` | The query makes a requirement mandatory, including an explicit numeric bound or an explicit required property. | `under $500`, `at least 4.5 stars`, `must be lightweight` |
| `soft_preference` | The wording expresses a non-mandatory preference that may influence ranking. Keep any stated numeric value and operator. | `affordable`, `highly rated`, `ideally under $400` |
| `product_attribute` | A product property is stated without enough wording to decide whether it is mandatory or merely preferred. | `waterproof`, `16 GB RAM`, `sulfate-free` |
| `negation` | The query explicitly excludes a product, property, or value. | `without fragrance`, `excluding Lenovo`, `except black` |
| `comparison` | The query requests a relative comparison, similarity, or substitute against a reference. | `cheaper than Brand A`, `similar to IKEA KIVIK`, `alternative to AirPods` |
| `ambiguous_expression` | The expression lacks a clear, operational criterion in its context. | `best value`, `good quality`, `near me` without a usable location |

## Annotation record

Each span annotation uses these fields:

| Field | Type and rule |
|---|---|
| `text` | Non-empty string copied from the query; it must match a contiguous span. |
| `label` | One of the six labels above. |
| `attribute` | Target field such as `price`, `hair_type`, or `rating`; use `null` only when it cannot be identified. |
| `operator` | One of `<`, `<=`, `>`, `>=`, `=`, `between`, `required`, `exclude`, or `near`; use `null` when no relation is expressed. |
| `value` | A number, string, range object, or `null`. Explicit numeric limits and categorical requirements must carry a value. A range uses `{"min": ..., "max": ...}`. |
| `unit` | Unit or currency such as `USD`, `THB`, `stars`, `kg`, or `days`; otherwise `null`. |
| `contextual_role` | Short snake_case description of the role, such as `maximum_price` or `required_feature`. |
| `confidence` | `high`, `medium`, or `low`. Low-confidence examples remain marked for human review. |

Numeric values are recorded even when they belong to a soft preference. For example, `ideally under $400` uses label `soft_preference`, operator `<=`, value `400`, and unit `USD`. A categorical requirement such as `must have Bluetooth` uses label `hard_constraint`, operator `required`, and value `Bluetooth`. An exclusion uses operator `exclude` and the excluded value.

## Context and precedence rules

1. Label the expression in the full query context, not from the lexicon entry alone.
2. Explicit force words such as `must`, `need`, and `only` make a requirement hard when they clearly apply to the product attribute.
3. `prefer`, `ideally`, and `preferably` make the attached requirement a soft preference. Preserve an explicit number, operator, and unit.
4. Subjective terms such as `affordable`, `cheap`, `good`, and `best` do not create numeric thresholds. Do not invent a budget or objective criterion.
5. A bare property such as `lightweight laptop` is a `product_attribute`; `I prefer a lightweight laptop` is a `soft_preference`; `the laptop must be lightweight` is a `hard_constraint`.
6. A product claim such as `non-stick` or `sulfate-free` is a `product_attribute`. A query-level exclusion such as `without fragrance` is a `negation`.
7. Use `comparison` for reference-based or relative intent. When a relative comparison includes an explicit numeric threshold, label the numeric bound as `hard_constraint` or `soft_preference` according to its wording.
8. Use `ambiguous_expression` when the meaning or criterion cannot be made operational from the query. Set `needs_clarification` only when that ambiguity prevents a useful search without more user input.
9. Do not infer missing requirements, budgets, units, certifications, or product properties. Context may resolve an explicit reference such as `preferably less` to a prior numeric bound; record that value only when the reference is unambiguous.
10. Span annotations must not overlap. If two separate requirements occur, annotate their separate spans.

## Projection to the V1 query intent object

The V1 query intent object keeps its agreed top-level fields: `original_query`, `normalized_query`, `language`, `query_type`, `product_category`, `attributes`, `constraints`, `soft_preferences`, `ambiguities`, and `needs_clarification`.

| Span label | Intent representation |
|---|---|
| `hard_constraint` | Add a `constraints` item with `priority: "hard"`. Map `<`, `<=`, `>`, `>=`, and `=` to `lt`, `lte`, `gt`, `gte`, and `eq`. Keep `between`, `required`, and `exclude` as written. |
| `soft_preference` | Add a `soft_preferences` item. Use `field`, `source_text`, and `preference`; include `operator`, `value`, and `unit` whenever the preference states a bound or target. |
| `product_attribute` | Add an `attributes` item with `name` and normalized `value`. |
| `negation` | Add a hard `constraints` item with `operator: "exclude"` and the excluded value. |
| `comparison` | Add a `soft_preferences` item with `relation`, `reference`, and `source_text`; explicit numeric bounds are represented as constraints or numeric soft preferences instead. |
| `ambiguous_expression` | Add an `ambiguities` item with `text`, `attribute`, and `reason`. Set `needs_clarification` according to rule 8 above. |

Example soft preference objects:

```json
{
  "field": "price",
  "preference": "low_price",
  "source_text": "affordable"
}
```

```json
{
  "field": "price",
  "preference": "preferred_bound",
  "operator": "lte",
  "value": 400,
  "unit": "USD",
  "source_text": "ideally under $400"
}
```

Comparison and ambiguity item examples:

```json
{
  "relation": "similar_to",
  "reference": "IKEA KIVIK",
  "source_text": "similar to the IKEA KIVIK"
}
```

```json
{
  "text": "best value",
  "attribute": "value",
  "reason": "criteria_unspecified"
}
```

## Dataset review status

The current 98 query examples are constructed seed examples and all have `annotation_status: requires_human_review`. The validation and split outputs are development artifacts; they are not gold-standard training or evaluation data until the annotations are reviewed and adjudicated.
