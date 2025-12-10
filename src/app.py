from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import types
from src.exceptions import TestException
from src.routes import router, templates


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router=router)


# @app.exception_handler(TestException)
# async def test_exception_handler(request: Request, exc: TestException):
#     redirect_home_url = request.url_for("home")

#     return templates.TemplateResponse
