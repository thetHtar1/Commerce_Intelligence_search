# E-commerce Query Understanding: Exploratory Research

**Project:** AI-Powered E-commerce Search & Ranking Engine  
**Research area:** Query Understanding  
**Status:** Exploratory research / preliminary findings  
**Platforms observed:** Amazon, TikTok Shop, Lazada, Shopee  
**Product category tested:** Shampoo  
**Currency context:** Thai Baht (THB)

---

## 1. Research Purpose

The purpose of this research is to understand how existing e-commerce platforms interpret user search queries and represent users' product requirements in their search results.

The initial focus is on whether a platform can understand more than a product name. In particular, this research examines whether search systems can recognize:

- Product category
- Product attributes and intended use
- Price-related requirements
- Multiple requirements expressed in one query
- The relationship between the query and the products shown in the search results

The research also considers whether the observed search experience differs between web and mobile app interfaces.

This is an exploratory platform audit based on manual searches. It is not a controlled benchmark of the platforms' underlying algorithms.

## 2. Research Method

The initial platform audit used shampoo-related queries across four e-commerce platforms.

### 2.1 Platforms

| Platform | Interface / context recorded |
|---|---|
| Amazon | Search results observed during manual testing |
| TikTok Shop | Web search without login and mobile app search were compared for the price-query test |
| Lazada | Search results observed during manual testing |
| Shopee | Search results observed during manual testing |

> The original spreadsheet does not record every platform's login state, exact test timestamp, region configuration, sorting state, or the full list of displayed products. These details should be captured in any follow-up experiment.

### 2.2 Initial Queries

The spreadsheet recorded these four queries:

1. `Shampoo`
2. `Shampoo for dry hair`
3. `Best shampoo for hair fall`
4. `Affordable shampoo for sensitive scalp`

A further price-constraint test was discussed separately:

5. `Affordable shampoo under 200 baht`

The fifth query is important because it tests whether a specific maximum price expressed in natural language is respected by the search results.

## 3. Observed Platform Behavior

The following findings preserve the observations from the original spreadsheet and the additional manual-test notes.

### 3.1 Amazon

| Query | Observation |
|---|---|
| `Shampoo` | Products were shown with rating signals and an Overall Pick item appeared prominently. |
| `Shampoo for dry hair` | Sponsored items appeared. Related search options were shown, and products associated with dry hair and hydrating ingredients could be retrieved. |
| `Best shampoo for hair fall` | Sponsored items or Overall Pick items appeared prominently. Hair-fall-related products and products with hair-fall protection claims could be retrieved. |
| `Affordable shampoo for sensitive scalp` | Overall Pick or sponsored items appeared first. Products associated with sensitive scalp could be retrieved, including products whose details mentioned sensitive scalp. The meaning of `Affordable` did not appear to be clearly reflected in the results. |

**Additional price-query observation**

For `Affordable shampoo under 200 baht`, products priced above ฿200 appeared among the top results. This suggests that the explicit price requirement was not consistently reflected in the observed top results.

**Initial interpretation**

Amazon appeared capable of retrieving products associated with some product attributes and intended uses. However, the observed results raised questions about how price requirements are interpreted and how sponsored or promoted placements interact with query relevance.

This observation does not establish how Amazon's internal ranking or advertising systems work.

### 3.2 TikTok Shop

| Query | Observation |
|---|---|
| `Shampoo` | Products with Mall tags, high ratings, and high sold counts appeared prominently. |
| `Shampoo for dry hair` | Products with high ratings could be retrieved, including products associated with dry hair and hydrating ingredients. |
| `Best shampoo for hair fall` | High-rated and high-selling products appeared prominently. Hair-fall context could be retrieved, including anti-hair-fall shampoo products. |
| `Affordable shampoo for sensitive scalp` | Products associated with sensitive scalp could be retrieved. However, the `Affordable` context was not clearly reflected, and the result pattern appeared somewhat inconsistent. |

**Additional price-query observation: web vs mobile app**

For the query `Shampoo under 200 baht` / `Affordable shampoo under 200 baht`:

- **Web, without logging in:** The results appeared to understand the under-฿200 requirement better.
- **Mobile app:** Some products priced above ฿200 appeared among the top five results.

This is a preliminary observation. The web and app tests may differ in login state, personalization, session history, interface behavior, or other conditions. Those variables need to be controlled before concluding that the two interfaces use different query-understanding or ranking strategies.

**Initial interpretation**

TikTok Shop appeared able to retrieve products associated with product attributes and intended use. The price-query test suggests a possible difference between web and app experiences, or between query interpretation and final result ordering.

The observed Mall, rating, and sold-count signals are visible product information. They do not prove which signals are used internally by the ranking system.

### 3.3 Lazada

| Query | Observation |
|---|---|
| `Shampoo` | Products were displayed with rating as a visible ordering signal. |
| `Shampoo for dry hair` | Products could be retrieved when relevant details were present in the product description. |
| `Best shampoo for hair fall` | Product details and rating sorting were observed. When promotions were available, discounted products appeared more prominently. |
| `Affordable shampoo for sensitive scalp` | Products associated with sensitive scalp could be retrieved, with rating used as a visible sorting signal. |

**Additional price-query observation**

For `Affordable shampoo under 200 baht`, products priced above ฿200 appeared among the top results.

**Initial interpretation**

The observations suggest that product-description content can help retrieve attribute-related products. However, the explicit price requirement did not consistently match the prices of the top results in the manual test.

This does not establish whether the cause was query interpretation, ranking, promotion placement, or another factor.

### 3.4 Shopee

| Query | Observation |
|---|---|
| `Shampoo` | Products were shown with rating, discount, and delivery-time information as visible signals. |
| `Shampoo for dry hair` | The first result from the initial `Shampoo` search continued to appear prominently. Some results were dry shampoo, which is not necessarily the same as shampoo intended for dry hair. |
| `Best shampoo for hair fall` | The initial search's first item continued to appear prominently. Hair-fall-related and anti-hair-fall products could also be retrieved and sorted by rating. |
| `Affordable shampoo for sensitive scalp` | The initial search's first item continued to appear prominently. Products with descriptions associated with sensitive scalp could be retrieved. It was unclear whether the `Affordable` requirement was understood. |

**Additional price-query observation**

For `Affordable shampoo under 200 baht`, products priced above ฿200 appeared among the top results.

**Additional repeated-result observation**

The first product shown for the initial broad query, `Shampoo`, continued to appear in later, more specific searches.

The tester suspected that these repeated products might be sponsored or limited-time offer items. However, their actual placement type was not confirmed. They should therefore be recorded as repeated top results, not classified as sponsored unless the platform visibly labels them as such.

**Initial interpretation**

The observations raise two separate questions:

1. Does the search system distinguish between similar-looking but different concepts, such as `dry shampoo` and `shampoo for dry hair`?
2. How much does a product's prominence in a broad search affect its position in later, more specific searches?

The repeated result alone does not reveal the underlying reason. It could be related to promotion, popularity, relevance, personalization, or other ranking factors.

---

## 4. Cross-Platform Findings

The following table summarizes the preliminary observations.

| Research dimension | Amazon | TikTok Shop | Lazada | Shopee |
|---|---|---|---|---|
| Basic product query | Shampoo products retrieved | Shampoo products retrieved | Shampoo products retrieved | Shampoo products retrieved |
| Dry-hair context | Hydrating / dry-hair-related products observed | Hydrating / dry-hair-related products observed | Description-dependent retrieval observed | Dry shampoo also appeared, creating possible intent mismatch |
| Hair-fall context | Hair-fall-related products retrieved | Anti-hair-fall products retrieved | Related products/details observed | Hair-fall-related products retrieved |
| Sensitive-scalp context | Related product details observed | Related products retrieved | Related products retrieved | Related product descriptions observed |
| `Affordable` context | Not clearly reflected | Not clearly reflected | Not established clearly | Not established clearly |
| Under-฿200 query | Products above ฿200 appeared in top results | Web appeared more responsive; app top five included products above ฿200 | Products above ฿200 appeared in top results | Products above ฿200 appeared in top results |
| Other notable observation | Sponsored / Overall Pick placements | Web and app results appeared inconsistent for price query | Rating and promotion signals visible | Initial top product repeated in later queries |

### 4.1 Finding: Attribute Retrieval Is Not the Same as Full Intent Understanding

The platforms could retrieve products associated with terms such as:

- Dry hair
- Hair fall
- Sensitive scalp

However, this does not necessarily mean that all requirements in a query were understood and satisfied together.

For example:

`Affordable shampoo for sensitive scalp`

contains at least two product requirements:

- Product attribute: suitable for sensitive scalp
- Price preference: affordable

A result may match the sensitive-scalp context while failing to demonstrate that the price preference was considered.

### 4.2 Finding: Explicit Price Constraints Need Separate Evaluation

The query:

`Affordable shampoo under 200 baht`

contains both a subjective price preference (`Affordable`) and an explicit numerical constraint (`under 200 baht`).

These should not be treated as identical:

- `Affordable` is subjective and may require context or a user-defined budget.
- `Under 200 baht` expresses a specific maximum price.

In the manual tests, products above ฿200 appeared among the top results on Amazon, Lazada, and Shopee. TikTok Shop appeared more responsive on web while its app's top five still included products above ฿200.

This raises a key system-design question: should an explicit numerical price constraint be enforced as a hard filter rather than merely influencing ranking?

For this project, the proposed behavior is:

- An explicit maximum price such as `under ฿200` should be parsed into a structured maximum-price constraint.
- Products above that maximum should be excluded from the eligible result set, unless the system explicitly explains that no matching products are available or the user chooses to relax the constraint.
- A subjective term such as `affordable` should not be silently converted into an arbitrary fixed price. The system should use available context, ask for a budget, or treat it as a soft preference.

This is a proposed design requirement for our system, not a claim about how existing platforms implement price filtering.

### 4.3 Finding: Query-Specific Relevance May Compete with Other Result Signals

The manual observations include visible signals such as:

- Sponsored labels
- Overall Pick labels
- Mall tags
- Ratings
- Sold counts
- Discounts
- Delivery time
- Product-description content

These signals may influence what users see, but the manual audit cannot identify the internal ranking formula or the relative weight of each signal.

The Shopee repeated-result observation is particularly useful for follow-up testing: a product that appears first for a broad query also appeared prominently in later, more specific searches. We need to determine whether this is caused by a promotion label, popularity, personalization, or insufficient query-specific relevance.

### 4.4 Finding: Web and App Experiences May Differ

TikTok Shop showed a possible difference between web search without login and mobile app search for the under-฿200 query.

This should be investigated separately from query understanding. Search behavior can be affected by:

- Login state
- User history and personalization
- Session state
- Location and currency
- Interface-specific filters or sorting
- Sponsored or promoted placements
- Differences in the displayed product set

The current observation is not sufficient to attribute the difference to a particular cause.

---

## 5. Problem Statement

E-commerce search systems allow users to search for products using product names and descriptive requirements. However, the manual platform audit suggests that retrieving products associated with individual query terms does not always result in products that satisfy the user's complete shopping intent.

A query may contain several requirements at once, including a product category, product attributes, intended use, and price constraints. The observed platforms could retrieve products related to attributes such as dry hair, hair fall, and sensitive scalp. Nevertheless, the results did not consistently demonstrate that all query requirements were satisfied together.

Price-related queries exposed a particularly important issue. When searching for `Affordable shampoo under 200 baht`, products priced above ฿200 appeared among the top results on Amazon, Lazada, and Shopee. TikTok Shop appeared to handle the price query better on web without login, while products above ฿200 still appeared in the mobile app's top five results.

The audit also identified possible relevance issues beyond price. For example, Shopee displayed dry shampoo for the query `Shampoo for dry hair`, even though dry shampoo and shampoo intended for dry hair describe different product concepts. The first product from the broad `Shampoo` search also continued to appear prominently in later, more specific searches.

These observations suggest a gap between matching individual query terms and understanding and enforcing the complete set of requirements expressed by a user.

**Therefore, this project will investigate how an e-commerce search system can convert short keywords and natural-language product queries into structured, explicit search intent, distinguish hard constraints from soft preferences, and use that intent to retrieve and rank products that better satisfy the user's requirements.**

---

## 6. Research Questions

### Main Research Question

**How can query understanding improve the interpretation and satisfaction of user requirements in e-commerce product search?**

### Supporting Research Questions

- **RQ1:** How can an e-commerce search system identify product categories, attributes, intended use, and price requirements from short and natural-language queries?
- **RQ2:** How can the system distinguish hard constraints, such as `under ฿200`, from soft preferences, such as `affordable`?
- **RQ3:** How can the system distinguish semantically similar but different product concepts, such as `dry shampoo` and `shampoo for dry hair`?
- **RQ4:** How should structured query intent guide product retrieval, filtering, and ranking?
- **RQ5:** How consistent are search results for the same query across web and mobile app interfaces, and what variables may explain observed differences?

RQ5 is a platform-audit question. It may be treated as a separate investigation rather than part of the core model evaluation.

---

## 7. Preliminary Research Hypotheses

These hypotheses are proposed from the manual observations. They have not yet been statistically tested.

- **H1 — Multi-attribute intent:** A query-understanding component that extracts multiple product requirements into structured fields will represent user intent more explicitly than using the raw query alone.
- **H2 — Hard price constraints:** Treating explicit numerical price limits as hard constraints will reduce the number of returned products that violate those limits.
- **H3 — Attribute distinction:** Distinguishing related but different product concepts will reduce semantically incorrect matches, such as returning dry shampoo for a query about shampoo for dry hair.
- **H4 — Query-aware retrieval and ranking:** Using structured query intent during retrieval and ranking will improve result relevance compared with relying only on broad product-keyword matching.
- **H5 — Interface consistency:** The same query may produce different results across web and app contexts; controlled tests are required to determine whether this difference persists when login state and other conditions are matched.

---

## 8. Agreed V1 Query Intent Schema

The project will use the following JSON object as its initial query-intent contract. It preserves the original query, records its normalized form, and separates product attributes, hard constraints, soft preferences, and ambiguities.

```json
{
  "original_query": "shampoo for dry hair under 200 baht",
  "normalized_query": "shampoo for dry hair under 200 baht",
  "language": "en",
  "query_type": "natural_language",
  "product_category": "shampoo",
  "attributes": [
    {
      "name": "hair_type",
      "value": "dry"
    }
  ],
  "constraints": [
    {
      "field": "price",
      "operator": "lte",
      "value": 200,
      "unit": "THB",
      "priority": "hard",
      "source_text": "under 200 baht"
    }
  ],
  "soft_preferences": [],
  "ambiguities": [],
  "needs_clarification": false
}
```

| Field | Purpose |
|---|---|
| `original_query` | Preserve the user's input for traceability. |
| `normalized_query` | Store the normalized query text used by downstream search components. |
| `language` | Record the identified language; the example uses `en`. |
| `query_type` | Classify the query form; the example uses `natural_language`. |
| `product_category` | Identify the requested product category. |
| `attributes` | Store product attributes as `name` and `value` pairs. |
| `constraints` | Store requirements with a field, operator, value, unit, priority, and source text. A `hard` constraint such as `price <= 200 THB` determines product eligibility. |
| `soft_preferences` | Store non-binding preferences that can influence ranking. |
| `ambiguities` | Record unresolved interpretations in the query. |
| `needs_clarification` | Indicate whether the user should clarify the query before search proceeds. |

The example maps `dry hair` to the `hair_type: dry` attribute and `under 200 baht` to a hard upper-price constraint. Retrieval should enforce hard constraints; ranking may use soft preferences to order eligible products. The example establishes the top-level fields and the shown attribute and constraint objects. The item formats for non-empty `soft_preferences` and `ambiguities`, along with allowed values for fields such as `query_type`, `operator`, and `priority`, should be formalized with the implementation's validation rules.

### Important design principles

1. Do not invent requirements that the user did not provide.
2. Preserve the original query for traceability.
3. Separate explicit constraints from subjective preferences.
4. Do not assume that `affordable` means a fixed price without supporting context.
5. Interpret `under ฿200` as a maximum-price constraint.
6. Represent multiple attributes separately rather than collapsing them into one vague text field.
7. If a query is ambiguous, preserve the ambiguity or request clarification instead of silently guessing.
8. Query understanding should produce structured intent; product retrieval and ranking should use that structure to find and order actual products.

---

## 9. Proposed Project Scope

The initial Query Understanding scope will focus on:

- Short product queries, such as `shampoo`
- Attribute-based queries, such as `shampoo for dry hair`
- Intended-use queries, such as `best shampoo for hair fall`
- Multi-attribute queries, such as `affordable shampoo for sensitive scalp`
- Explicit price constraints, such as `shampoo under 200 baht`
- Distinguishing similar product concepts, such as `dry shampoo` versus `shampoo for dry hair`

The project will not assume that every user writes long natural-language sentences. It should support short keywords and more descriptive queries.

The project will initially focus on query understanding and its connection to retrieval and ranking. A full personalized recommendation system is outside this document's immediate scope.

---

## 10. Limitations of the Current Research

The current findings are exploratory and should not be presented as proof that one platform is universally better or worse than another.

Limitations include:

- Only one product category, shampoo, was tested.
- The number of query examples is small.
- The audit was performed manually rather than using a large search-log dataset.
- The exact top-result product lists and product positions were not consistently recorded in the original spreadsheet.
- Screenshots and timestamps were not included for every observation.
- Login state, location, session history, sorting, and personalization settings were not fully controlled across platforms.
- Sponsored, promoted, or special placements cannot always be identified unless the platform explicitly labels them.
- Search results can change over time.
- The internal query-understanding and ranking algorithms of the platforms are not known from these observations.

For these reasons, statements in this document describe what was observed during manual testing. They do not claim to explain the platforms' internal implementations.

---

## 11. Next Research and Development Steps

Before implementing the Query Understanding component:

1. Preserve the current platform observations and, where possible, attach screenshots of the first five results for each query.
2. Record product title, displayed price, result position, visible sponsored/promotional labels, and whether each explicit requirement is satisfied.
3. Repeat the price-query test with the same query, location, currency, sorting, and login state wherever possible.
4. For TikTok Shop, compare web and app while matching login state and other available conditions.
5. Create a small set of manually reviewed queries and expected structured intents using the agreed V1 schema.
6. Expand testing beyond shampoo while preserving the same intent contract.
7. Use this set to test whether the Query Understanding component extracts category, attributes, intended use, price constraints, and preferences correctly.

Validate the agreed V1 schema against the reviewed query set, then pass the structured intent to the retrieval and ranking components.

---

## 12. Conclusion

The initial platform audit suggests that current e-commerce search experiences can retrieve products associated with several descriptive attributes, but the top results do not always demonstrate that the user's complete requirements have been satisfied.

The most useful observations for this project concern explicit price constraints, the distinction between similar product concepts, repeated top products across more specific queries, and possible differences between web and app search experiences.

These observations motivate a Query Understanding component that converts user input into structured intent, distinguishes hard constraints from soft preferences, and provides clear requirements to downstream retrieval and ranking components. The project adopts the JSON object in Section 8 as its initial intent contract.

**The next development focus is to validate this intent contract with manually reviewed queries and connect it to the retrieval and ranking components.**
