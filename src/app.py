from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api import router as api_router
from src.config import huey
from src.routes import router


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router=router)
app.include_router(router=api_router)
