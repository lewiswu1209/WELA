
import json
import requests

from typing import Dict
from typing import List
from typing_extensions import Annotated
from autogen_core.tools import FunctionTool

def __format_result(result_str_list: List[str]) -> str:
    border = "=" * 40
    middle_sep = "-" * 40
    return f"{border}\n{middle_sep.join(result_str_list)}\n{border}"

def __google_search(
    query: Annotated[str, "Search query string. For best results: 1) Prioritize searching with English keywords, as English content is usually more abundant and updated more timely, especially in technical and academic fields; 2) Use specific keywords instead of vague phrases; 3) Use quotation marks \"exact phrases\" to force matching; 4) Use site:domain to limit to a specific website; 5) Use -exclude words to filter results; 6) Use OR to connect alternative words; 7) Prioritize professional terms; 8) Keep 2-5 keywords for balanced results; 9) Choose the appropriate language according to the target content (use Chinese only when looking for specific Chinese resources). Examples: 'climate change report 2024 site:gov -opinion' or '\"machine learning algorithms\" tutorial (Python OR Julia)'"]
) -> str:

    response = requests.get(
        url="https://sear.guxyz.com/search",
        params={'q': query, 'format': 'json'},
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        },
        verify=False,
        cookies={
            "disabled_engines": "wikipedia__general\054currency__general\054wikidata__general\054duckduckgo__general\054lingva__general\054startpage__general\054dictzone__general\054mymemory translated__general\054brave__general"
        }
    )

    if response.status_code == 200:
        try:
            data = response.json()
            results: List[Dict] = data.get('results', [])

            result_str_list: List[str] = []
            for result in results:
                result_str_list.append(f"""Title: {result.get("title", "")}
Url: {result.get("url", "")}
Snippet: {result.get("content", "")}
"""
                )
            return __format_result(result_str_list)
        except json.JSONDecodeError as e:
            return f"JSON parsing failed: {repr(e)}"
    else:
        return f"HTTP {response.status_code}"

GoogleSearchTool = FunctionTool(
    func=__google_search,
    name="google_search",
    description="Use the Google search engine to query real-time online information and return search results including titles, links, and summaries. Suitable for scenarios that require obtaining the latest information, finding materials on specific topics, researching current events, or verifying facts.",
    strict=True
)
