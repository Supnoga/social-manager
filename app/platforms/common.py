import json
import os

import httpx

from .. import db

PORT = int(os.environ.get("SM_PORT", "8765"))
BASE_URL = f"http://localhost:{PORT}"


class PlatformError(Exception):
    pass


def client(timeout=120):
    return httpx.Client(timeout=httpx.Timeout(timeout, connect=30), follow_redirects=True)


def save_tokens(account_id, tokens):
    db.run("UPDATE accounts SET tokens=? WHERE id=?", (json.dumps(tokens), account_id))


def tokens(account):
    t = account.get("tokens") or "{}"
    return json.loads(t) if isinstance(t, str) else t


def check(r, what):
    if r.status_code >= 400:
        try:
            body = r.json()
        except Exception:
            body = r.text[:500]
        raise PlatformError(f"{what}: HTTP {r.status_code} {json.dumps(body, ensure_ascii=False)[:600]}")
    return r


def text_for(video, platform, account=None):
    """Text príspevku podľa siete, krajiny a jazyka (pravidlá v captions.py, bez AI)."""
    from .. import captions
    b = captions.build(video, platform, account)
    return b["title"], b["text"]


def file_chunks(path, start=0, end=None, size=1024 * 1024 * 4):
    with open(path, "rb") as f:
        f.seek(start)
        remaining = (end - start) if end is not None else None
        while True:
            n = size if remaining is None else min(size, remaining)
            if n <= 0:
                break
            b = f.read(n)
            if not b:
                break
            if remaining is not None:
                remaining -= len(b)
            yield b
