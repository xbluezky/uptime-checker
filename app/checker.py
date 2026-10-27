import time

import httpx


async def check_url(client: httpx.AsyncClient, url: str) -> dict:
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=5.0, follow_redirects=True)
        ok, code = resp.status_code < 400, resp.status_code
    except httpx.HTTPError:
        ok, code = False, None
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    return {"url": url, "ok": ok, "status_code": code, "latency_ms": latency_ms}