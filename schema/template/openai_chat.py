
import os
import base64
import mimetypes

from io import BytesIO
from abc import ABC
from abc import abstractmethod
from PIL import Image
from PIL import ImageGrab

from typing import Any
from typing import List
from typing import Union
from typing import Optional

from schema.prompt.openai_chat import ToolCall
from schema.prompt.openai_chat import ImageURL
from schema.prompt.openai_chat import TextContent
from schema.prompt.openai_chat import ImageContent
from schema.prompt.openai_chat import Message
from schema.prompt.openai_chat import AIMessage
from schema.prompt.openai_chat import UserMessage
from schema.prompt.openai_chat import ToolMessage
from schema.prompt.openai_chat import SystemMessage
# from schema.template.openai_chat import ContentTemplate
# from schema.template.openai_chat import TextContentTemplate
# from schema.template.openai_chat import UserMessageTemplate
# from schema.template.openai_chat import ImageContentTemplate
from schema.template.prompt_template import PromptTemplate
from schema.template.prompt_template import StringPromptTemplate

def __resize_image(image: Image.Image, max_width: int = 600, max_height: int = 450) -> Image.Image:
    """
    Resize an image to fit within the specified maximum width and height while maintaining the aspect ratio.

    Parameters:
    - image (Image.Image): PIL Image object.
    - max_width (int): Maximum width for the resized image. Default is 800 pixels.
    - max_height (int): Maximum height for the resized image. Default is 600 pixels.

    Returns:
    - Image.Image: Resized image object.
    """
    width_ratio = max_width / image.width
    height_ratio = max_height / image.height
    ratio = min(width_ratio, height_ratio)
    
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)
    
    resized_img = image.resize((new_width, new_height), Image.LANCZOS)
    resized_img.format = image.format
    return resized_img

def encode_image(image_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Encode an image file to a Base64 string after resizing it to fit within the specified dimensions.

    Parameters:
    - image_path (str): Path to the image file.
    - encoding (str): The encoding to use for the Base64 string. Default is 'utf-8'.

    Returns:
    - Optional[str]: Base64 encoded string of the image, or None if the image cannot be processed.
    """
    if not os.path.exists(image_path):
        return None
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None or not mime_type.startswith('image'):
        return None
    
    try:
        with Image.open(image_path) as img:
            resized_image = __resize_image(img)
        
        buffered = BytesIO()
        resized_image.save(buffered, format=resized_image.format)
        encoded_string = base64.b64encode(buffered.getvalue()).decode(encoding)
        return f"data:{mime_type};base64,{encoded_string}"
    except IOError as _:
        return None

def encode_clipboard_image(encoding: str = 'utf-8') -> Optional[str]:
    """
    Encode an image from the clipboard to a Base64 string after resizing it to fit within the specified dimensions.

    Parameters:
    - encoding (str): The encoding to use for the Base64 string. Default is 'utf-8'.

    Returns:
    - Optional[str]: Base64 encoded string of the image, or None if no image is found in the clipboard.
    """
    try:
        image = ImageGrab.grabclipboard()
        if image is None or not isinstance(image, Image.Image):
            return None
        
        resized_image = __resize_image(image)
        
        buffered = BytesIO()
        resized_image.save(buffered, format=resized_image.format)
        mime_type = Image.MIME[resized_image.format]
        encoded_string = base64.b64encode(buffered.getvalue()).decode(encoding)
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as _:
        return None

class TextContentTemplate(PromptTemplate):

    def __init__(self, template: StringPromptTemplate) -> None:
        self.__template: StringPromptTemplate = template

    def format(self, **kwargs: Any) -> Any:
        if self.__template is None:
            return None
        text_content = TextContent(text=self.__template.format(**kwargs), type="text")
        return text_content

class ImageContentTemplate(PromptTemplate):

    def __init__(self, image_url: str = None, key: str = None, detail: str = "low") -> None:
        self.__key: str = key
        self.__image_url: str = image_url
        self.__detail = detail

    def format(self, **kwargs: Any) -> Any:
        image_content = None
        if self.__image_url:
            image_url = ImageURL(url=self.__image_url, detail=self.__detail)
            image_content = ImageContent(image_url=image_url, type="image_url")
        elif self.__key and kwargs.get(self.__key, None):
            image_url = ImageURL(url=kwargs.get(self.__key, None), detail=self.__detail)
            image_content = ImageContent(image_url=image_url, type="image_url")

        return image_content

class ContentTemplate(PromptTemplate):
    def __init__(self, templates: List[PromptTemplate]) -> None:
        self.__templates: List[PromptTemplate] = templates

    def format(self, **kwargs: Any) -> Any:
        content_list = []
        for template in self.__templates:
            content = template.format(**kwargs)
            if content:
                content_list.append(content)
        return content_list

class MessageTemplate(ABC):
    @abstractmethod
    def to_message(self, **kwargs: Any) -> Message:
        pass

class MessagePlaceholder:
    def __init__(self, placeholder_key: str) -> None:
        self.__placeholder_key = placeholder_key

    @property
    def placeholder_key(self) -> str:
        return self.__placeholder_key

class ToolMessageTemplate(MessageTemplate):
    def __init__(self, template: PromptTemplate, tool_call_id: str) -> None:
        self.__template = template
        self.__tool_call_id = tool_call_id

    def to_message(self, **kwargs: Any) -> AIMessage:
        if self.__tool_call_id:
            return ToolMessage(role="tool", content=self.__template.format(**kwargs), tool_call_id=self.__tool_call_id)
        else:
            return ToolMessage(role="tool", content=self.__template.format(**kwargs))

class AIMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: StringPromptTemplate = None,
        name: str = None,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        self.__template = template
        self.__name = name
        self.__tool_calls = tool_calls

    def to_message(self, **kwargs: Any) -> AIMessage:
        message = AIMessage(role="assistant")
        if self.__template:
            message["content"] = self.__template.format(**kwargs)
        if self.__name:
            message["name"] = self.__name
        if self.__tool_calls:
            message["tool_calls"] = self.__tool_calls
        return message

class SystemMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: StringPromptTemplate,
        name: str = None
    ) -> None:
        self.__template = template
        self.__name = name

    def to_message(self, **kwargs: Any) -> Message:
        if self.__name:
            return SystemMessage(
                content=self.__template.format(**kwargs),
                role="system",
                name=self.__name
            )
        else:
            return SystemMessage(
                content=self.__template.format(**kwargs),
                role="system"
            )

class UserMessageTemplate(MessageTemplate):

    def __init__(
        self,
        template: Union[PromptTemplate, ContentTemplate],
        name: str = None
    ) -> None:
        self.__template = template
        self.__name = name

    def to_message(self, **kwargs: Any) -> Message:
        if self.__name:
            return UserMessage(
                content=self.__template.format(**kwargs),
                role="user",
                name=self.__name
            )
        else:
            return UserMessage(
                content=self.__template.format(**kwargs),
                role="user"
            )

class ChatTemplate(PromptTemplate):

    def __init__(self, message_template_list: List[MessageTemplate]) -> None:
        self.__message_template_list: List[MessageTemplate] = []
        for message_template in message_template_list:
            self.__message_template_list.append(message_template)

    def format(self, **kwargs: Any) -> Any:
        messages = []
        for message_template in self.__message_template_list:
            if isinstance(message_template, MessagePlaceholder):
                messages.extend(kwargs.get(message_template.placeholder_key))
            elif isinstance(message_template, MessageTemplate):
                message = message_template.to_message(**kwargs)
                messages.append(message)
        return messages

__all__ = [
    "encode_image",
    "encode_clipboard_image",
    "TextContentTemplate",
    "ImageContentTemplate",
    "ContentTemplate",
    "MessageTemplate",
    "MessagePlaceholder",
    "ToolMessageTemplate",
    "AIMessageTemplate",
    "SystemMessageTemplate",
    "UserMessageTemplate",
    "ChatTemplate"
]
