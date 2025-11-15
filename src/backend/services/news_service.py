import json
import httpx
import logging

try:
    from .config import config
except ImportError:
    from config import config

# Configure logging
logger = logging.getLogger(__name__)

# Create a shared httpx client for connection pooling
_http_client = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client():
    """Close the shared HTTP client"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


async def get_news(query: str) -> dict:
    """Fetches news data from SearchAPI.io"""
    base_url: str = config.base_api_url
    news_params: dict = config.default_news_params.copy()
    news_params.update(
        {"q": query}
    )
    headers: dict = {
        "Authorization": f"Bearer {config.serp_key}"
    }

    logger.info("📰 NEWS SERVICE: get_news called")
    logger.info(f"   Query: {query}")

    try:
        client = get_http_client()
        response = await client.get(url=base_url, params=news_params, headers=headers)
        
        if response.status_code == 200:
            news_data: dict = response.json()
            with open('news_data.json', 'w') as f:
                json.dump(news_data, f)
            logger.info(f"   ✅ Found {len(news_data.get('organic_results', []))} news articles")
            return news_data
        else:
            logger.error(f"   ❌ API returned status code: {response.status_code}")
            return {}
    except httpx.HTTPError as e:
        logger.error(f"   ❌ Request failed: {e}", exc_info=True)
        print(e)
        return {}

def parse_news_data(news_json: dict) -> tuple[str, dict]:
    """
    Returns (toon_string, full_data_dict)
    - toon_string: Lightweight format for LLM reasoning
    - full_data_dict: Complete news data with images, links, thumbnails for UI
    """
    organic_results = news_json.get('organic_results', [])

    # TOON: Compact format for agent to analyze and filter
    news_toon = f"""news_articles [{len(organic_results)}] {{idx, title, source, date, snippet}}\n"""

    # Full data: Everything the UI will need
    full_data = {'articles': []}

    for idx, article in enumerate(organic_results, 1):
        # Extract key information for TOON
        title = article.get('title', 'N/A')
        source = article.get('source', 'N/A')
        date = article.get('date', 'N/A')
        snippet = article.get('snippet', 'N/A')

        # TOON line: Only essentials for comparison
        news_toon += f"\t\t{idx},{title},{source},{date},{snippet}\n"

        # Full data: Complete information including links, thumbnails, images
        full_data['articles'].append({
            "idx": idx,  # For agent to reference this article
            "position": article.get('position'),
            "title": title,
            "link": article.get('link', ''),
            "source": source,
            "date": date,
            "snippet": snippet,
            "favicon": article.get('favicon', ''),
            "thumbnail": article.get('thumbnail', '')
        })

    return news_toon, full_data


if __name__ == "__main__":
    import asyncio
    
    async def test():
        query: str = "Recent developments on AI bubble"
        news_data = await get_news(query)
        print(f"Keys: {list(news_data.keys())}")

        if news_data:
            toon, full_data = parse_news_data(news_data)
            print("\n=== TOON FORMAT (for Agent) ===")
            print(toon)
            print("\n=== FULL DATA (for UI) ===")
            print(f"Found {len(full_data['articles'])} articles")
            if full_data['articles']:
                print(f"Sample article: {full_data['articles'][0]['title']}")
                print(f"Link: {full_data['articles'][0]['link']}")
        
        await close_http_client()
    
    asyncio.run(test())

