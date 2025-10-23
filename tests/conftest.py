import json
import os
from contextlib import contextmanager, asynccontextmanager
from subprocess import check_call
from typing import Any, AsyncContextManager, Callable, Dict, Optional, Type
import asyncio
import uvicorn

import pytest
import pytest_asyncio

from wapiti_arsenic import Session, browsers, get_session, services
from tests.utils import find_binary
from .app import build_app


def local_session_factory(
    name: str,
    driver: str,
    service: Type[services.Service],
    browser: Type[browsers.Browser],
    browser_opts: Optional[Dict[str, Any]] = None,
) -> Callable[[str], AsyncContextManager[Session]]:
    browser_opts = browser_opts or {}

    def ctx(root_url: str):
        binary = find_binary(driver)
        return get_session(service(binary=binary), browser(**browser_opts), root_url)

    ctx.__name__ = name
    return ctx


if os.environ.get("APPVEYOR", "false") == "True":
    _extra_ff_opts = {"binary": r"C:\Program Files\Mozilla Firefox\firefox.exe"}
else:
    _extra_ff_opts = {}


get_ff_session = local_session_factory(
    "get_ff_session",
    "geckodriver",
    services.Geckodriver,
    browsers.Firefox,
    {"moz:firefoxOptions": {"args": ["-headless"], **_extra_ff_opts}},
)
get_chrome_session = local_session_factory(
    "get_chrome_session",
    "chromedriver",
    services.Chromedriver,
    browsers.Chrome,
    {"goog:chromeOptions": {"args": ["--headless", "--disable-gpu", "--no-sandbox"]}},
)
get_ie_session = local_session_factory(
    "get_ie_session",
    "IEDriverServer",
    services.IEDriverServer,
    browsers.InternetExplorer,
)
get_edge_session = local_session_factory(
    "get_edge_session", "msedgedriver", services.MSEdgeDriver, browsers.Edge
)


@contextmanager
def bsl_context():
    if "BROWSERSTACK_LOCAL_IDENTIFIER" not in os.environ:
        raise pytest.skip(
            "Browserstack API key set, but no local identifier configured (BROWSERSTACK_LOCAL_IDENTIFIER)"
        )
    binary = find_binary("BrowserStackLocal")
    if not binary:
        raise pytest.skip(
            "Browserstack API key set, but no BrowserStackLocal binary found"
        )
    args = [
        binary,
        "--key",
        os.environ["BROWSERSTACK_API_KEY"],
        "--verbose",
        os.environ.get("BROWSERSTACK_LOCAL_VERBOSITY", "1"),
        "--local-identifier",
        os.environ["BROWSERSTACK_LOCAL_IDENTIFIER"],
        "--daemon",
    ]
    check_call(args + ["start"])
    try:
        yield
    finally:
        check_call(args + ["stop"])


@asynccontextmanager
async def get_remote_session(root_url: str):
    if "REMOTE_BROWSER" not in os.environ:
        raise pytest.skip("No remote browser configured (REMOTE_BROWSER)")
    if "REMOTE_SERVICE" not in os.environ:
        raise pytest.skip("No remote service configured (REMOTE_SERVICE)")
    if "BROWSERSTACK_API_KEY" not in os.environ:
        raise pytest.skip("No browserstack api key configured (BROWSERSTACK_API_KEY)")
    remote_browser = json.loads(os.environ["REMOTE_BROWSER"])
    browser_cls = getattr(browsers, remote_browser["browserName"])
    with bsl_context():
        async with get_session(
            services.Remote(url=os.environ["REMOTE_SERVICE"]),
            browser_cls(**remote_browser),
            root_url,
        ) as session:
            yield session


@pytest_asyncio.fixture(
    params=[get_ff_session, get_chrome_session, get_remote_session, get_ie_session],
    ids=lambda func: func.__name__.split("_")[1],
)
async def session(root_url, request) -> Session:
    async with request.param(root_url) as s:
        yield s


@pytest_asyncio.fixture
async def root_url():
    app = build_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=0)
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.01)

    try:
        host, port = server.servers[0].sockets[0].getsockname()
        yield f"http://{host}:{port}"
    finally:
        server.should_exit = True
        await task
