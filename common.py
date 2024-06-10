
import os
import yaml
import base64
import mimetypes

from io import BytesIO
from PIL import Image
from PIL import ImageGrab
from typing import Optional
from qdrant_client import QdrantClient

from agents.meta import Meta
from callback.callback import ToolCallback
from models.openai_chat import OpenAIChat
from toolkit.quit import Quit
from toolkit.toolkit import Toolkit
from toolkit.weather import Weather
from toolkit.definition import Definition
from toolkit.browsing.browsing import Browsing
from memory.window_qdrant_memory import WindowQdrantMemory

def build_meta(config_file_path: str = "config.yaml", callback: ToolCallback = None):
    with open(config_file_path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if config.get("proxy", None):
        proxies = {
            "http": config.get("proxy"),
            "https": config.get("proxy")
        }
    else:
        proxies = None

    if config.get("memory", None):
        memory_key = config.get("memory").get("memory_key", "memory")
        limit = config.get("memory").get("limit", 15)
        window_size = config.get("memory").get("window_size", 5)
        score_threshold = config.get("memory").get("score_threshold", 0.6)
        if config.get("memory").get("qdrant").get("type") == "cloud":
            qdrant_client = QdrantClient(
                url=config.get("memory").get("qdrant").get("url"),
                api_key=config.get("memory").get("qdrant").get("api_key")
            )
        elif config.get("memory").get("qdrant").get("type") == "local":
            qdrant_client = QdrantClient(
                path=config.get("memory").get("qdrant").get("path")
            )
        else:
            qdrant_client = QdrantClient(":memory:")

        memory = WindowQdrantMemory(
            memory_key=memory_key, 
            qdrant_client=qdrant_client,
            limit=limit,
            window_size=window_size,
            score_threshold=score_threshold
        )
    else:
        memory = None

    meta_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=True, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    tool_model = OpenAIChat(model_name=config.get("openai").get("model_name"),stream=False, api_key=config.get("openai").get("api_key"), base_url=config.get("openai").get("base_url"))
    toolkit = Toolkit([Quit(), Weather(), Definition(proxies), Browsing(tool_model, proxies)], callback)

    return Meta(model=meta_model, prompt=config.get("prompt"),memory=memory, toolkit=toolkit)

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
