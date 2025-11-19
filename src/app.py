from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routes import router


app = FastAPI()
app.include_router(router=router)


@app.get("/index")
def index():
    return "Hello World!"
