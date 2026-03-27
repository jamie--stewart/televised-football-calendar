from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.bunkr_ui.routes import album, proxy, search
from src.bunkr_ui.settings import BunkrSettings

BASE_DIR = Path(__file__).resolve().parent
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.settings = BunkrSettings()
    app.state.http_client = httpx.AsyncClient(
        headers={"User-Agent": CHROME_USER_AGENT},
        timeout=httpx.Timeout(app.state.settings.request_timeout),
        follow_redirects=True,
    )
    app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    yield
    await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="Bunkr UI", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.include_router(search.router)
    app.include_router(album.router)
    app.include_router(proxy.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
