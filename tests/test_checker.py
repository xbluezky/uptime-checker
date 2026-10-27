import asyncio

import httpx

from app.checker import check_url


def run(handler):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return await check_url(c, "http://x.test")

    return asyncio.run(go())


def test_ok_200():
    r = run(lambda req: httpx.Response(200))
    assert r["ok"] is True and r["status_code"] == 200


def test_server_error_500():
    r = run(lambda req: httpx.Response(500))
    assert r["ok"] is False and r["status_code"] == 500


def test_connection_error():
    def boom(req):
        raise httpx.ConnectError("boom")

    r = run(boom)
    assert r["ok"] is False and r["status_code"] is None


def test_not_modified_304_is_ok():
    r = run(lambda req: httpx.Response(304))
    assert r["ok"] is True and r["status_code"] == 304