from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio
from main import create_app

config = Config()
config.bind = ["0.0.0.0:8000"]
config.worker_class = "asyncio"
config.workers = 4

app = create_app()

if __name__ == "__main__":
    asyncio.run(serve(app, config))
