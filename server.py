import contextlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from echo_server import mcp as echo_mcp
from math_server import mcp as math_mcp
import os


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(echo_mcp.session_manager.run())
        await stack.enter_async_context(math_mcp.session_manager.run())
        yield


BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    space_host = os.environ.get("SPACE_HOST")
    if space_host and space_host.strip():
        base_url = space_host.strip().rstrip("/")
    else:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
    return templates.TemplateResponse("index.html", {"request": request, "base_url": base_url})

app.mount("/echo", echo_mcp.streamable_http_app())
app.mount("/math", math_mcp.streamable_http_app())

PORT = int(os.environ.get("PORT", "10000"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
