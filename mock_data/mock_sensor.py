import asyncio
import random
import signal
import sys
from typing import Optional

import httpx
import argparse

API_URL_DEFAULT = "http://127.0.0.1:8000/api/v1/sensor-data"

def gen_payload() -> dict:
    return {
        "soil_moisture": round(random.uniform(10.0, 40.0), 2),
        "ph": round(random.uniform(5.5, 7.5), 2),
        "wind_speed": round(random.uniform(0.0, 10.0), 2),
    }

async def post_once(client: httpx.AsyncClient, url: str) -> None:
    payload = gen_payload()
    r = await client.post(url, json=payload, timeout=5.0)
    r.raise_for_status()
    print("POSTed", payload)

async def run(url: str, interval: float, count: Optional[int]) -> None:
    stop = asyncio.Event()

    def _stop(*_):
        if not stop.is_set():
            stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _stop)

    async with httpx.AsyncClient() as client:
        i = 0
        while not stop.is_set():
            try:
                await post_once(client, url)
            except Exception as e:
                print(f"[warn] post failed: {e}")
            i += 1
            if count is not None and i >= count:
                break
            # küçük jitter ile daha gerçekçi aralık
            jitter = random.uniform(-0.2, 0.2) * interval
            await asyncio.sleep(max(0.1, interval + jitter))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=API_URL_DEFAULT)
    p.add_argument("--interval", type=float, default=5.0, help="seconds")
    p.add_argument("--count", type=int, default=None, help="kaç adet gönderileceği (sonsuz için boş bırak)")
    args = p.parse_args()

    try:
        asyncio.run(run(args.url, args.interval, args.count))
    except KeyboardInterrupt:
        sys.exit(0)
