"""
agents.py
Multi-agent semantic search using OpenAI Agents SDK (pip install openai-agents).

Architecture (MVP — 2 agents, sequential):
  ┌────────────────┐     ParsedQuery      ┌──────────────┐
  │ Query Parser   │ ──────────────────▶  │ Search Agent │
  │ (structured    │   (Pydantic model)   │ (tool call)  │
  │  output)       │                      │              │
  └────────────────┘                      └──────┬───────┘
        ▲                                        │
        │ user_query                              │ search_products()
        │                                        ▼
  recommend()                           Qdrant hybrid search
  (orchestrator)                        + natural language response

Key SDK concepts used:
  - Agent(output_type=ParsedQuery) → LLM returns structured Pydantic model
  - @function_tool → registers a Python function as an agent tool
  - Runner.run(agent, input) → async execution, returns RunResult
  - RunResult.final_output → the agent's final response (str or Pydantic)
"""

from __future__ import annotations

from pydantic import BaseModel
from agents import Agent, Runner, function_tool

from src.shared.embedding import MODEL as EMBEDDING_MODEL, get_embedding
from src.shared.logging import setup_logger
from src.shared.vector_store import get_vector_store

logger = setup_logger("agents")

COLLECTION = "products"


# ---------------------------------------------------------------------------
# Structured output model for Query Parser
# ---------------------------------------------------------------------------
class ParsedQuery(BaseModel):
    """Structured representation of a user's product search query."""

    semantic_query: str
    """Text for vector similarity search (e.g. 'red dress')"""

    price_min: float | None = None
    """Minimum price filter (JPY)"""

    price_max: float | None = None
    """Maximum price filter (JPY)"""

    sort_by_price: str | None = None
    """'asc' for cheapest first, 'desc' for most expensive first, None for relevance"""

    category: str | None = None
    """Product category filter"""


# ---------------------------------------------------------------------------
# Agent 1: Query Parser
# ---------------------------------------------------------------------------
QUERY_PARSER_INSTRUCTIONS = """\
You are a query parser for a Japanese e-commerce product search system.
Analyze the user's natural language query and extract structured search parameters.

Rules:
- semantic_query: The core product description for vector search. Remove price/budget info.
- price_min / price_max: Extract explicit price constraints in JPY. Only set when numbers are mentioned.
- sort_by_price: Set to "asc" if the user wants cheap/affordable items, "desc" for expensive/luxury.
  Only set when there is a clear price preference WITHOUT a specific number.
- category: Extract product category if mentioned (e.g. "ドレス", "シャツ", "靴").
- All currency values must be in JPY. If a non-JPY currency is used, respond with JPY only and
  set semantic_query to include the original currency mention.

Examples:
- "赤いドレスで5000円以下" → semantic_query="赤いドレス", price_max=5000, category="ドレス"
- "安いTシャツ" → semantic_query="Tシャツ", sort_by_price="asc", category="Tシャツ"
- "高級な革靴" → semantic_query="高級な革靴", sort_by_price="desc", category="靴"
- "summer outfit" → semantic_query="summer outfit"
"""

query_parser_agent = Agent(
    name="Query Parser",
    instructions=QUERY_PARSER_INSTRUCTIONS,
    output_type=ParsedQuery,
    model="gpt-4o-mini",
)


# ---------------------------------------------------------------------------
# Agent 2: Search Agent (with tool)
# ---------------------------------------------------------------------------
def _search_products_structured(
    query: str,
    price_min: float | None = None,
    price_max: float | None = None,
    category: str | None = None,
    sort_by_price: str | None = None,
) -> list[dict]:
    """Core search logic returning structured product data.

    Hybrid Search flow:
      1. query text → OpenAI embedding (1536-dim vector)
      2. Build Qdrant payload filter from price/category params
      3. Qdrant cosine similarity search + payload filter (= Hybrid Search)
      4. Optional client-side sort by price (for "安い"/"高級" intents)
      5. Return structured list of product dicts with similarity_score
    """
    logger.info(
        "search_products query=%s price_min=%s price_max=%s category=%s sort=%s",
        query, price_min, price_max, category, sort_by_price,
    )

    # 1. Generate embedding for query
    query_vector = get_embedding(query)

    # 2. Build filters
    filters = {}
    if price_min is not None:
        filters["price_min"] = price_min
    if price_max is not None:
        filters["price_max"] = price_max
    if category:
        filters["category"] = category

    # 3. Qdrant hybrid search
    store = get_vector_store()
    results = store.search(
        collection=COLLECTION,
        query_vector=query_vector,
        limit=5,
        filters=filters if filters else None,
    )

    if not results:
        return []

    # 4. Sort by price if requested
    if sort_by_price == "asc":
        results.sort(key=lambda r: r["payload"].get("price", float("inf")))
    elif sort_by_price == "desc":
        results.sort(key=lambda r: r["payload"].get("price", 0), reverse=True)

    # 5. Build structured output
    products = []
    for r in results:
        p = r["payload"]
        products.append({
            "product_id": p.get("product_id", ""),
            "name": p.get("name", ""),
            "category": p.get("category", ""),
            "price": p.get("price", 0),
            "image_url": p.get("image_url", ""),
            "description": p.get("description", ""),
            "available_stock": p.get("available_stock", 0),
            "similarity_score": round(r["score"], 4),
        })
    return products


def _search_products_impl(
    query: str,
    price_min: float | None = None,
    price_max: float | None = None,
    category: str | None = None,
    sort_by_price: str | None = None,
) -> str:
    """Text-formatted search results for Search Agent (calls _search_products_structured)."""
    products = _search_products_structured(query, price_min, price_max, category, sort_by_price)

    if not products:
        return "No products found matching your criteria."

    lines = []
    for p in products:
        lines.append(
            f"- {p['name']} | \u00a5{p['price']:,.0f} | {p['category']} | "
            f"score={p['similarity_score']:.3f} | stock={p['available_stock']}"
        )
    return "\n".join(lines)


@function_tool
def search_products(
    query: str,
    price_min: float | None = None,
    price_max: float | None = None,
    category: str | None = None,
    sort_by_price: str | None = None,
) -> str:
    """Search products using semantic similarity and optional price/category filters.

    Args:
        query: Semantic search text to find similar products.
        price_min: Minimum price filter in JPY.
        price_max: Maximum price filter in JPY.
        category: Product category filter.
        sort_by_price: 'asc' for cheapest first, 'desc' for most expensive first.
    """
    return _search_products_impl(query, price_min, price_max, category, sort_by_price)


SEARCH_AGENT_INSTRUCTIONS = """\
You are a product search assistant for a Japanese e-commerce platform.
Use the search_products tool to find products based on the parsed query parameters.
Present the results in a helpful, natural way in the same language as the original query.
If no results are found, suggest broadening the search criteria.
"""

search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_AGENT_INSTRUCTIONS,
    tools=[search_products],
    model="gpt-4o-mini",
)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
async def recommend(user_query: str) -> dict:
    """Run the 2-agent pipeline: parse → search → response.

    Called from POST /products/recommend endpoint.
    Step 1: Query Parser Agent parses NL query into ParsedQuery (structured output).
    Step 2a: Direct search for structured product data (for API response).
    Step 2b: Search Agent generates natural language summary (for UX).

    Returns dict with: query, model_version, products (structured), recommendations (NL text).
    """
    logger.info("recommend query=%s", user_query)

    # Step 1: Parse user query into structured form
    parse_result = await Runner.run(query_parser_agent, user_query)
    parsed: ParsedQuery = parse_result.final_output
    logger.info("parsed=%s", parsed.model_dump_json())

    # Step 2a: Get structured product data directly
    products = _search_products_structured(
        query=parsed.semantic_query,
        price_min=parsed.price_min,
        price_max=parsed.price_max,
        category=parsed.category,
        sort_by_price=parsed.sort_by_price,
    )

    # Step 2b: Search Agent generates NL response
    search_input = (
        f"Search for products with these parameters: "
        f"query='{parsed.semantic_query}', "
        f"price_min={parsed.price_min}, "
        f"price_max={parsed.price_max}, "
        f"category={parsed.category}, "
        f"sort_by_price={parsed.sort_by_price}"
    )
    search_result = await Runner.run(search_agent, search_input)

    return {
        "query": user_query,
        "model_version": EMBEDDING_MODEL,
        "products": products,
        "recommendations": search_result.final_output,
    }
