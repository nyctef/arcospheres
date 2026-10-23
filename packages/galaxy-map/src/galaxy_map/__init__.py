from pathlib import Path

from livereload import Server
from .app import app

def main() -> None:
    server = Server(app.wsgi_app)
    server.serve()


