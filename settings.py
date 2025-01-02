from pydantic import BaseModel
from cat.mad_hatter.decorators import plugin


class SearchRedditSettings(BaseModel):
    client_id: str = "_12P7oY0BIOSkoZo2ZbE7Q"
    client_secret: str = "rzCLT1l8fO6dnpHF6TjODl4XaLFsHw"
    posts_limit: int = 100
    comments_limit: int = 50


@plugin
def settings_schema():
    return SearchRedditSettings.schema()
