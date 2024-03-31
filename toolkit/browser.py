
from bs4 import element
from bs4 import BeautifulSoup
from typing import Any
from typing import List
from htmlmin import minify
from curl_cffi import requests

from toolkit import Tool

def extract_blank_tags(tag: element.Tag) -> None:
    children_to_remove = []
    for child in tag.contents:
        if isinstance(child, element.Comment):
            children_to_remove.append(child)
        elif isinstance(child, element.NavigableString):
            if not child.strip():
                children_to_remove.append(child)
        elif isinstance(child, element.Tag):
            if len(child.contents) == 0:
                children_to_remove.append(child)
            else:
                extract_blank_tags(child)
    for child in children_to_remove:
        child.extract()

def extract_tags(tag: element.Tag, tag_names: List[str] = ["script", "noscript", "style", "iframe", "br", "path", "symbol", "svg", "use", "ul", "li", "nav", "img", "footer", "header"]) -> None:
    for unwanted_tag in tag.find_all(name=tag_names):
        unwanted_tag.extract()

def minify_html(html_content: str) -> str:
    return minify(html_content, remove_comments=True, remove_empty_space=True)

def unwrap_tags(tag: element.Tag, tag_names: List[str] = ["strong", "span"]) -> None:
    for unwrapped_tags in tag.find_all(tag_names):
        unwrapped_tags.unwrap()

def tag_to_text_with_return(tag: element.Tag) -> str:
    txt = ""
    for child in tag.contents:
        if isinstance(child, element.NavigableString):
            txt += child.text + "\n"
        elif isinstance(child, element.Tag):
            txt += tag_to_text_with_return(child)
    return txt

class Browser(Tool):

    def __init__(self) -> None:
        super().__init__(
            name="browser",
            description="A web browser for visiting a specific URL.",
            required=["url"],
            url={
                "type": "string",
                "description": "The url to visit.",
            }
        )

    def _invoke(self, **kwargs: Any) -> str:
        try:
            url: str = kwargs["url"]
            html_content: str = requests.get(url=url, impersonate="chrome101").content.decode("utf-8")
            html_content = minify_html(html_content)
            soup = BeautifulSoup(html_content, "html.parser")
            body = soup.body
            unwrap_tags(body)
            extract_tags(body)
            extract_blank_tags(body)
            return tag_to_text_with_return(body)
        except Exception as e:
            return f"{e}"

__all__ = [
    "Browser"
]
