# Query Understanding: Intent Schema & Constraint Extraction

## 1. Purpose

This document defines the scope for designing the Query Understanding
component of the **AI-Powered E-commerce Search & Ranking Engine**.

The component converts a user's product search query into structured
information that downstream retrieval and ranking components can use. It
must preserve the user's stated requirements without inventing missing
preferences or constraints.

## 2. Scope

This phase covers two connected areas:

1.  **Intent Schema Design** --- defining the structured representation
    of a search query.
2.  **Constraint Extraction** --- defining how explicit requirements and
    preferences are identified, classified, and represented.

The work will first be documented and reviewed. Python implementation
and automated validation will follow after the schema and extraction
rules are agreed.

## 3. Intent Schema Design

The schema should represent the following information:

  -----------------------------------------------------------------------
  Field                               Description
  ----------------------------------- -----------------------------------
  `original_query`                    The exact query entered by the
                                      user.

  `normalized_query`                  A normalized form used for search
                                      processing, without changing the
                                      user's intent.

  `language`                          The detected language of the query.

  `query_type`                        The query category, such as
                                      keyword, attribute, or natural
                                      language.

  `product_category`                  The product category the user is
                                      searching for, when identifiable.

  `attributes`                        Product attributes or use-context
                                      information expressed in the query.

  `constraints`                       Explicit requirements that must be
                                      satisfied.

  `soft_preferences`                  Preferences that can influence
                                      ranking but should not
                                      automatically exclude products.

  `ambiguities`                       Parts of the query whose meaning
                                      cannot be determined reliably.

  `confidence`                        A confidence representation for
                                      extracted information, where
                                      supported.

  `needs_clarification`               Whether clarification is needed
                                      before safely applying an uncertain
                                      interpretation.
  -----------------------------------------------------------------------

The final field types, allowed values, and null/empty-value conventions
will be specified in the schema documentation.

### 3.1 Query types

The initial design should support:

-   **Keyword query:** `shampoo`
-   **Attribute query:** `sulfate-free shampoo`
-   **Natural-language query:** `shampoo for dry hair under 200 baht`

The system should support short product-name and category searches as
well as descriptive queries. It should not force every query into a
natural-language interpretation.

## 4. Constraint Extraction

Constraint extraction identifies requirements and preferences expressed
in the query and converts them into structured representations.

### 4.1 Hard constraints

Hard constraints are explicit requirements that a product must satisfy.
They may be used as retrieval filters or eligibility conditions.

  Query phrase                 Expected interpretation
  ---------------------------- ---------------------------------
  `under 200 baht`             Maximum price of 200 THB
  `above 100 baht`             Minimum price of 100 THB
  `between 100 and 300 baht`   Price range from 100 to 300 THB
  `sulfate-free shampoo`       Sulfate-free requirement

### 4.2 Soft preferences

Soft preferences describe qualities the user would prefer. They can
influence ranking, but should not automatically exclude otherwise
relevant products.

  -----------------------------------------------------------------------
  Query phrase                        Expected interpretation
  ----------------------------------- -----------------------------------
  `affordable shampoo`                Prefer lower-priced products

  `popular shampoo`                   Prefer products with popularity
                                      signals

  `highly rated shampoo`              Prefer products with stronger
                                      rating signals

  `good quality shampoo`              Quality preference; the meaning may
                                      be ambiguous
  -----------------------------------------------------------------------

A subjective term such as `affordable` must not be converted into an
arbitrary fixed price limit. If the user has not supplied a budget, the
system must not invent one.

### 4.3 Product attributes and use context

Some query information describes the product or the user's intended use
rather than a numeric constraint.

-   `shampoo for dry hair` --- hair type / suitability attribute.
-   `dry shampoo` --- a distinct product type, not necessarily shampoo
    for dry hair.

The extraction logic must preserve this distinction and avoid treating
similar wording as equivalent when the meanings differ.

## 5. Edge Cases to Address

1.  **Price operators:** distinguish terms such as `under`, `below`,
    `less than`, and `at most`.
2.  **Approximate prices:** define how to represent phrases such as
    `around 200 baht`.
3.  **Mixed preferences:** handle phrases such as
    `cheap but high quality` without assuming an unstated budget or
    quality definition.
4.  **Similar product concepts:** distinguish `dry shampoo` from
    `shampoo for dry hair`.
5.  **Missing budget:** do not create a price constraint when the user
    has not stated one.
6.  **Multiple constraints:** support queries containing more than one
    requirement or preference.
7.  **Ambiguous wording:** preserve uncertainty and request
    clarification only when needed to interpret or apply the query
    safely.

## 6. Design Principles

-   **Preserve user intent:** extracted fields must be supported by the
    original query.
-   **Do not invent requirements:** never infer an unstated budget,
    brand, attribute, or product requirement.
-   **Separate filtering from ranking:** hard constraints determine
    eligibility; soft preferences influence ranking.
-   **Preserve the original query:** normalization must not erase or
    alter the user's meaning.
-   **Represent uncertainty:** ambiguous or unsupported interpretations
    should remain unresolved rather than being guessed.
-   **Keep components decoupled:** query understanding structures
    intent; retrieval finds candidate products; ranking orders
    candidates.

## 7. Expected Deliverables

### Documentation

-   `docs/query_intent_schema.md`
    -   Schema fields and definitions
    -   JSON representation
    -   Data types and allowed values
    -   Null and empty-value conventions
    -   Example query-to-schema outputs
-   `docs/constraint_extraction_rules.md`
    -   Hard-constraint classification rules
    -   Soft-preference classification rules
    -   Attribute and use-context extraction rules
    -   Price operator handling
    -   Ambiguity and edge-case handling
    -   Positive and negative examples

### Technical design outputs

-   A reviewed JSON structure for query intent.
-   A documented set of constraint classification rules.
-   Query examples with expected extraction results.
-   Validation requirements for later implementation.

## 8. Out of Scope for This Documentation Phase

-   Implementing the query parser in Python.
-   Selecting or training an LLM or NLP model.
-   Building multilingual translation pipelines.
-   Connecting query understanding to BM25 or vector retrieval.
-   Implementing ranking models.
-   Measuring search quality on a production dataset.

These may be addressed in later implementation phases.

## 9. Completion Criteria

This phase is complete when:

-   The intent schema fields and their meanings are documented.
-   Hard constraints and soft preferences are clearly distinguished.
-   Product attributes are distinguished from product categories and
    constraints.
-   The listed edge cases have documented handling rules or are
    explicitly marked as unresolved.
-   Representative query examples have expected structured outputs.
-   The documentation is reviewed and committed to the project
    repository.

## 10. Next Step

After the scope is reviewed, create the two detailed documents:

1.  `docs/query_intent_schema.md`
2.  `docs/constraint_extraction_rules.md`

Only after these documents are stable should the project move to Python
implementation and schema validation.
