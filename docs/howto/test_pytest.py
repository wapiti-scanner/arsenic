import asyncio

import pytest
import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from wapiti_arsenic import browsers, services, start_session, stop_session

pytestmark = pytest.mark.asyncio


async def index(request):
    if request.method == "POST":
        data = await request.form()
        name = data.get("name", "World")
    else:
        name = "World"
    return HTMLResponse(
        f"""<html>
    <body>
        <h1>Hello {name}</h1>
        <form method='post' action='/'>
            <input name='name' />
            <input type='submit' />
        </form>
    </body>
</html>"""
    )


def build_app():
    routes = [Route("/", index, methods=["GET", "POST"])]
    return Starlette(routes=routes)


@pytest.fixture
async def app():
    application = build_app()
    config = uvicorn.Config(application, host="127.0.0.1", port=0)
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


@pytest.fixture
async def session(app):
    session = await start_session(services.Geckodriver(), browsers.Firefox(), bind=app)
    try:
        yield session
    finally:
        await stop_session(session)


async def test_index(session):
    await session.get("/")
    title = await session.wait_for_element(5, "h1")
    text = await title.get_text()
    assert text == "Hello World"
    form_field = await session.get_element('input[name="name"]')
    await form_field.send_keys("test")
    submit = await session.get_element('input[type="submit"]')
    await submit.click()
    title = await session.wait_for_element(5, "h1")
    text = await title.get_text()
    assert text == "Hello test"
