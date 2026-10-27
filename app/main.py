import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app import db
from app.checker import check_url

log = logging.getLogger("uptime")
TARGETS = [u for u in os.getenv("TARGETS", "https://example.com").split(",") if u]
INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))


async def check_loop(client: httpx.AsyncClient) -> None:
    while True:
        try:
            results = await asyncio.gather(*(check_url(client, u) for u in TARGETS))
            for r in results:
                await asyncio.to_thread(db.save, r)
        except Exception:
            log.exception("check cycle failed")
        await asyncio.sleep(INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(db.init_db)
    async with httpx.AsyncClient() as client:
        task = asyncio.create_task(check_loop(client))
        yield
        task.cancel()


app = FastAPI(title="uptime-checker", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    return await asyncio.to_thread(db.latest)