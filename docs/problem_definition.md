# Problem Definition

## 1. What problem are we solving?

When users shop on e-commerce platforms, they often have specific needs but do not always know how to find the most suitable products.

For example, a user may want to buy a gentle shampoo under $20 for dry hair. They need to search for products, understand product specifications, check product reviews, and compare different options before making a purchase decision.

However, users often need to switch between e-commerce platforms and external tools such as ChatGPT or Google to research products and compare information.

This creates a fragmented shopping experience and makes product discovery and decision-making more difficult.

Our project aims to solve this problem by improving how users search for, retrieve, and evaluate products within an e-commerce platform.

## 2. Why is traditional e-commerce search insufficient?

Traditional e-commerce search mainly depends on keyword matching and predefined filters.

This approach has several limitations:

- **Limited understanding of user intent:** It may not fully understand the meaning behind natural-language queries.
- **Keyword dependency:** Users may need to know the exact product name or keywords to find relevant results.
- **Limited semantic understanding:** Products with different wording but similar meanings may not appear together.
- **Weak requirement matching:** Traditional search may not effectively consider multiple requirements, such as budget, product attributes, and user preferences simultaneously.
- **Difficult product comparison:** Users often need to open multiple product pages and manually compare their features.

As a result, users may spend more time searching and evaluating products before making a purchase decision.

## 3. Who are the target users?

Our primary target users are:

- **Online shoppers:** People who use e-commerce platforms to search for and purchase products.
- **Research-oriented shoppers:** Users who compare product specifications, reviews, prices, and features before purchasing.
- **Users with specific requirements:** People who have particular budgets, preferences, or product attributes in mind but may not know the exact product keywords.

The system is designed to support users with different shopping needs and levels of product knowledge.

## 4. What is our proposed solution?

We propose an AI-powered E-commerce Search and Ranking Engine that improves product discovery through natural-language understanding, hybrid retrieval, and machine learning-based ranking.

The system will include the following capabilities:

1. **Natural-language Query Understanding:** Understand user queries and extract structured shopping requirements using an LLM-based approach.
2. **Structured Search Intent:** Convert user requirements into structured information, including product category, budget, attributes, and preferences.
3. **Hybrid Product Retrieval:** Combine BM25 keyword search and vector-based semantic search to retrieve relevant products.
4. **Metadata Filtering:** Apply product attributes, price ranges, and category constraints.
5. **Feature Engineering:** Generate query-product relevance features to support product ranking.
6. **ML-based Ranking:** Rank retrieved products based on their relevance to user requirements.
7. **Search Evaluation:** Evaluate retrieval and ranking performance using information retrieval metrics.

The main objective is to make product search more relevant and efficient by understanding what users actually need rather than relying only on exact keyword matching.

## 5. What are the expected benefits?

### For users

- Find relevant products using natural-language queries.
- Spend less time searching with different keywords.
- Discover products that match their requirements.
- Receive more relevant product rankings.
- Make product selection and comparison easier.

### For e-commerce platforms

- Improve product search relevance.
- Increase the likelihood of users discovering suitable products.
- Provide a better product discovery experience.
- Build a foundation for future personalization and recommendation systems.

### Technical outcomes

- Develop an end-to-end hybrid search system.
- Demonstrate LLM-based query understanding.
- Implement and compare keyword and semantic retrieval.
- Build an ML-based product ranking model.
- Establish a measurable search evaluation framework.
- Develop a reusable data pipeline for search and ranking analytics.
