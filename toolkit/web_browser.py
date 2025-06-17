
import html2text

from typing import Any
from typing import Callable
from readability import Document
from playwright.sync_api import sync_playwright

from wela_agents.toolkit.toolkit import Tool

class WebBrowser(Tool):

    def __init__(self, headless=True, proxy: str = None) -> None:
        super().__init__(
            name="visit_webpage",
            description="A web browser for visiting a specific URL.",
            required=["url", "question"],
            url={
                "type": "string",
                "description": "The url to visit."
            }
        )
        self.__proxy = proxy
        self.__headless = headless
        self.__converter = html2text.HTML2Text()
        self.__converter.ignore_links = False
        self.__converter.ignore_images = False
        self.__converter.body_width = 0

    def __fetch_html_with_playwright(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.__headless,
                args=['--start-maximized'],
                proxy={
                    "server": self.__proxy
                } if self.__proxy else None
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()

            # 绕过 navigator.webdriver 检测
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            content = page.content()
            browser.close()
            return content

    def __extract_main_content(self, html: str) -> str:
        try:
            doc = Document(html)
            return doc.summary()
        except Exception:
            return html

    def __convert_to_markdown(self, html: str) -> str:
        return self.__converter.handle(html)

    def __visit(self, url: str) -> str:
        html = self.__fetch_html_with_playwright(url)
        main_content = self.__extract_main_content(html)
        markdown_content = self.__convert_to_markdown(main_content)
        return markdown_content

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        try:
            url: str = kwargs["url"]
            return self.__visit(url)

        except Exception as e:
            return f"{e}"

__all__ = [
    "WebBrowser"
]
