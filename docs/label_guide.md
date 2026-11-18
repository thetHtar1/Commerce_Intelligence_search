# Label Guide

| Label | Meaning | Example |
|---|---|---|
| `hard_constraint` | Mandatory condition or explicit numeric/categorical bound | `under $500`, `at least 4.5 stars`, `must be lightweight` |
| `soft_preference` | Ranking preference; non-matching items may still be considered | `affordable`, `highly rated`, `preferably under $500` |
| `product_attribute` | Product property/specification; strength may be unresolved | `waterproof`, `16 GB RAM`, `sulfate-free` |
| `negation` | Explicit exclusion or absence requirement | `without fragrance`, `excluding leather` |
| `comparison` | Relative comparison, similarity or substitute intent | `cheaper than $700`, `alternative to AirPods` |
| `ambiguous_expression` | Meaning or operational criterion is underspecified | `good quality`, `best value`, `not too expensive` |

Each span includes `text`, `label`, `attribute`, `operator`, `value`, `unit`, `contextual_role`, and `confidence`.
