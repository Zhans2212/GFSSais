from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings

hostname = "127.0.0.1"
port = 5200
LOG_PATH = "logs"
debug = True
PACKAGE_NAME = "DASORP_TEST"

templates = Jinja2Templates(directory="app/templates")

VERSION = "1.0.1"
templates.env.globals["version"] = VERSION

def setup_static(app):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

class Settings(BaseSettings):
    SSO_SERVER: str = "http://192.168.1.34:8825"
    SECRET_KEY: str = "7d5b9ab175d3368b65282ba456987df0aaeecc8c30949d6d7d290dba1"

settings = Settings()