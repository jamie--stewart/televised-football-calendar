from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class BunkrSettings(BaseSettings):
    model_config = ConfigDict(env_prefix="BUNKR_")

    host: str = "127.0.0.1"
    port: int = 8000
    search_base_url: str = "https://bunkr-albums.io"
    viewer_base_url: str = "https://bunkr.cr"
    cdn_domain: str = "bnkr.b-cdn.net"
    request_timeout: int = 15
    cache_ttl: int = 300
