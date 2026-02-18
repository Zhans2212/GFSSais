from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

def setup_static(app):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
