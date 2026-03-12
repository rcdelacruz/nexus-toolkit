import logging
from mcp.server.fastmcp import FastMCP
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import httpx
import bs4

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 5
MAX_CONTENT_LENGTH = 8000
MIN_CODE_ELEMENTS_THRESHOLD = 5
REQUEST_TIMEOUT = 15.0
SEARCH_TIMEOUT = 30.0


async def nexus_search(
    query: str,
    mode: str = "general",
    max_results: int = DEFAULT_MAX_RESULTS
) -> str:
    """
    A hybrid search tool combining Exa's breadth and Ref's specificity.

    Args:
        query: The search term.
        mode: 'general' for broad web search (Exa style).
              'docs' to prioritize technical documentation (Ref style).
        max_results: Number of results to return (1-20).

    Returns:
        Formatted search results with titles, URLs, and snippets.
    """
    logger.info(f"Search requested - Query: '{query}', Mode: {mode}, Max results: {max_results}")

    if not query or not query.strip():
        return "Error: Query cannot be empty"

    if mode not in ["general", "docs"]:
        return f"Error: Invalid mode '{mode}'. Must be 'general' or 'docs'"

    max_results = max(1, min(max_results, 20))

    final_query = query.strip()
    if mode == "docs":
        final_query += " site:readthedocs.io OR site:github.com OR site:stackoverflow.com OR documentation API"

    results = []
    try:
        with DDGS(timeout=SEARCH_TIMEOUT) as ddgs:
            ddg_results = list(ddgs.text(final_query, max_results=max_results))

            if not ddg_results:
                return "No results found. Try a different query or mode."

            for r in ddg_results:
                title = r.get('title', 'No title')
                url = r.get('href', 'No URL')
                snippet = r.get('body', 'No description')
                results.append(f"- [Title]: {title}\n  [URL]: {url}\n  [Snippet]: {snippet}")

            logger.info(f"Search successful - Found {len(results)} results")
            return "\n\n".join(results)

    except TimeoutError:
        return "Error: Search timed out. Please try again."
    except Exception as e:
        logger.exception(f"Unexpected error during search: {query}")
        return f"Error: Search failed: {str(e)}"


async def nexus_read(url: str, focus: str = "auto") -> str:
    """
    Reads a URL with intelligent parsing logic.

    Args:
        url: The URL to visit.
        focus:
            'general' = Returns clean article text (Exa style).
            'code'    = Returns only headers, code blocks, and tables (Ref style).
            'auto'    = Detects if it's a doc site and switches to 'code' mode.

    Returns:
        Parsed and cleaned content from the URL.
    """
    logger.info(f"Read requested - URL: '{url}', Focus: {focus}")

    if not url or not url.strip():
        return "Error: URL cannot be empty"

    if focus not in ["auto", "general", "code"]:
        return f"Error: Invalid focus '{focus}'. Must be 'auto', 'general', or 'code'"

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    if focus == "auto":
        technical_indicators = ["docs", "api", "reference", "github", "guide", "documentation"]
        if any(ind in url.lower() for ind in technical_indicators):
            focus = "code"
        else:
            focus = "general"

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "NexusMCP/1.0"},
        timeout=REQUEST_TIMEOUT
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            soup = bs4.BeautifulSoup(response.text, 'html.parser')

            for trash in soup.find_all(["script", "style", "nav", "footer", "iframe", "svg", "noscript"]):
                trash.decompose()

            output = []
            output.append(f"=== SOURCE: {url} ===")
            output.append(f"=== MODE: {focus.upper()} ===\n")

            if focus == "code":
                relevant_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'pre', 'code', 'table'])

                for tag in relevant_tags:
                    if tag.name in ['h1', 'h2', 'h3', 'h4']:
                        header_text = tag.get_text(strip=True)
                        if header_text:
                            output.append(f"\n## {header_text}")
                    elif tag.name == 'pre':
                        code_text = tag.get_text()
                        if code_text.strip():
                            output.append(f"```\n{code_text}\n```")
                    elif tag.name == 'code' and tag.parent.name != 'pre':
                        code_text = tag.get_text(strip=True)
                        if code_text:
                            output.append(f"`{code_text}`")
                    elif tag.name == 'table':
                        try:
                            rows = tag.find_all('tr')
                            if rows:
                                output.append("\n[Table]")
                                for row in rows[:10]:
                                    cells = row.find_all(['td', 'th'])
                                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                                    if cell_texts:
                                        output.append(" | ".join(cell_texts))
                        except Exception as table_error:
                            logger.warning(f"Table parsing failed: {table_error}")
                            output.append("\n[Table - parsing failed]")

                if len(output) < MIN_CODE_ELEMENTS_THRESHOLD:
                    return (
                        f"Code-focused extraction found minimal content ({len(output)} elements). "
                        "The page may not contain structured documentation. "
                        "Try focus='general' for better results."
                    )
            else:
                text = soup.get_text(separator='\n')
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                output.append("\n".join(lines))

            result = "\n".join(output)[:MAX_CONTENT_LENGTH]
            if len("\n".join(output)) > MAX_CONTENT_LENGTH:
                result += f"\n\n[Content truncated at {MAX_CONTENT_LENGTH} characters]"

            logger.info(f"Read successful - Extracted {len(result)} characters from {url}")
            return result

        except httpx.TimeoutException:
            return f"Error: Request timed out after {REQUEST_TIMEOUT}s"
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP error {e.response.status_code}: {e.response.reason_phrase}"
        except httpx.RequestError as e:
            return f"Error: Network error: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error reading {url}")
            return f"Error: Unexpected error reading URL: {str(e)}"


def register_search_tools(mcp: FastMCP) -> None:
    """Register nexus_search and nexus_read tools onto the MCP server."""
    mcp.tool()(nexus_search)
    mcp.tool()(nexus_read)
