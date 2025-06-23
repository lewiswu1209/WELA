
import io
import base64
import html2text

from io import BytesIO
from PIL import Image
from typing import Any
from typing import Callable
from readability import Document
from playwright.sync_api import sync_playwright

from wela_agents.agents.llm import LLMAgent
from wela_agents.toolkit.toolkit import Tool
from wela_agents.models.openai_chat import OpenAIChat
from wela_agents.schema.template.openai_chat import ChatTemplate
from wela_agents.schema.template.openai_chat import ContentTemplate
from wela_agents.schema.template.openai_chat import UserMessageTemplate
from wela_agents.schema.template.openai_chat import TextContentTemplate
from wela_agents.schema.template.openai_chat import ImageContentTemplate
from wela_agents.schema.template.prompt_template import StringPromptTemplate

class WebBrowser(Tool):

    def __init__(self, headless=True, proxy: str = None) -> None:
        super().__init__(
            name="visit_webpage",
            description="A web browser for visiting a specific URL.",
            required=["url"],
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

class WebBrowserScreenshot(Tool):

    def __init__(self, model: OpenAIChat, headless=True, proxy: str = None) -> None:
        super().__init__(
            name="screenshot_webpage",
            description="A web browser for visiting a specific URL. It has a high cost, so it can only be used when the `visit_webpage` tool cannot correctly retrieve the content.",
            required=["url"],
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

        self.__model = model

    def __screenshot_with_playwright(self, url: str) -> Image.Image:
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
            # 注入JS代码，选中所有满足尺寸要求的元素，并加红色边框
            page.evaluate("""
                Array.from(document.querySelectorAll('*')).forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 100 && rect.height > 140) {
                        el.style.border = '1px solid red';
                    }
                });
            """)
            image_bytes = page.screenshot(full_page=True)
            image = Image.open(io.BytesIO(image_bytes))
            browser.close()
            return image

    def __extract_main_content(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image.save(buffered, format=image.format)
        mime_type = Image.MIME[image.format]
        encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_string = f"data:{mime_type};base64,{encoded_string}"

        message_template_list = [
            UserMessageTemplate(
                ContentTemplate(
                    [
                        TextContentTemplate(StringPromptTemplate("Here is a screenshot of a webpage:")),
                        ImageContentTemplate(image_url=data_string),
                    ]
                )
            ),
            UserMessageTemplate(
                StringPromptTemplate(
'''You are tasked with summarizing the raw content of a webpage retrieved from a web search. Your goal is to create a concise summary that preserves the most important information from the original web page. This summary will be used by a downstream research agent, so it's crucial to maintain the key details without losing essential information.

Please follow these guidelines to create your summary:

1. Identify and preserve the main topic or purpose of the webpage.
2. Retain key facts, statistics, and data points that are central to the content's message.
3. Keep important quotes from credible sources or experts.
4. Maintain the chronological order of events if the content is time-sensitive or historical.
5. Preserve any lists or step-by-step instructions if present.
6. Include relevant dates, names, and locations that are crucial to understanding the content.
7. Summarize lengthy explanations while keeping the core message intact.

When handling different types of content:

- For news articles: Focus on the who, what, when, where, why, and how.
- For scientific content: Preserve methodology, results, and conclusions.
- For opinion pieces: Maintain the main arguments and supporting points.
- For product pages: Keep key features, specifications, and unique selling points.

Your summary should be comprehensive enough to stand alone as a source of information.

Remember, your goal is to create a summary that can be easily understood and utilized by a downstream research agent while preserving the most critical information from the original webpage.'''
                )
            )
        ]
        chat_template = ChatTemplate(message_template_list=message_template_list)
        agent = LLMAgent(model=self.__model, prompt_template=chat_template)
        return agent.predict()["content"]

    def __visit(self, url: str) -> str:
        screenshot = self.__screenshot_with_playwright(url)
        main_content = self.__extract_main_content(screenshot)

        return main_content

    def _invoke(self, callback: Callable = None, **kwargs: Any) -> str:
        try:
            url: str = kwargs["url"]
            return self.__visit(url)

        except Exception as e:
            return f"{e}"


__all__ = [
    "WebBrowser",
    "WebBrowserScreenshot"
]
