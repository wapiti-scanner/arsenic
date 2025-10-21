from pathlib import Path

import uvicorn
from jinja2 import Environment, FileSystemLoader
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

TEMPLATES_DIR = Path(__file__).parent / "templates"


async def process_form(request):
    return {"value": (await request.form()).get("field")}


async def process_cookies(request):
    return {"value": request.cookies.get("test", "")}


async def process_file_form(request):
    data = await request.form()
    return {
        "filename": data["file"].filename,
        "contents": (await data["file"].read()).decode("utf-8"),
    }


def render_view(jinja, template, process=None):
    async def view(request):
        data = {}
        if process is not None:
            data = await process(request)
        response = await jinja.get_template(template).render_async(**data)
        return HTMLResponse(response)

    return view


def build_app() -> Starlette:
    jinja = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), enable_async=True)
    routes = [
        Route("/", render_view(jinja, "index.html")),
        Route("/html/", render_view(jinja, "form.html")),
        Route("/form/", render_view(jinja, "data.html", process_form), methods=["POST"]),
        Route("/js/", render_view(jinja, "js.html")),
        Route("/cookie/", render_view(jinja, "data.html", process_cookies)),
        Route("/actions/", render_view(jinja, "actions.html")),
        Route("/screenshot/", render_view(jinja, "screenshot.html")),
        Route("/file/", render_view(jinja, "file_form.html")),
        Route(
            "/file/", render_view(jinja, "file_data.html", process_file_form), methods=["POST"]
        ),
        Route("/selectors/", render_view(jinja, "selector_types.html")),
    ]
    return Starlette(routes=routes)


def main():
    uvicorn.run(build_app(), host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
