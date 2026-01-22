# app/services/fetcher.py
import json
import time
from urllib.parse import urljoin

import requests


def fetch_stats(base_url: str, stats_path: str = "/api/stats", timeout_s: int = 8, retries: int = 1):
    """
    Returns dict:
      ok(bool), http_status(int|None), latency_ms(int|None),
      cpu_percent(float|None), mem_percent(float|None), disk_percent(float|None), swap_percent(float|None),
      raw_json(str|None), reason(str|None)
    """
    base = (base_url or "").rstrip("/") + "/"
    path = (stats_path or "/api/stats").lstrip("/")
    url = urljoin(base, path)

    last_latency = None

    for attempt in range(retries + 1):
        t0 = time.perf_counter()
        try:
            r = requests.get(url, timeout=timeout_s, headers={"Accept": "application/json"})
            latency_ms = int((time.perf_counter() - t0) * 1000)
            last_latency = latency_ms
            http_status = r.status_code

            if http_status != 200:
                # no retry for most HTTP codes (you can tweak)
                return {
                    "ok": False,
                    "http_status": http_status,
                    "latency_ms": latency_ms,
                    "cpu_percent": None,
                    "mem_percent": None,
                    "disk_percent": None,
                    "swap_percent": None,
                    "raw_json": None,
                    "reason": f"http_{http_status}",
                    "url": url,
                }

            data = r.json()  # may raise ValueError
            raw = json.dumps(data, ensure_ascii=False)

            if not isinstance(data, dict):
                return {
                    "ok": False,
                    "http_status": http_status,
                    "latency_ms": latency_ms,
                    "cpu_percent": None,
                    "mem_percent": None,
                    "disk_percent": None,
                    "swap_percent": None,
                    "raw_json": raw,
                    "reason": "json_not_object",
                    "url": url,
                }

            cpu = _get_first_number(data, ["cpu_percent", "cpu", "cpuUsage", "cpu_usage"])
            mem = _get_first_number(data, ["mem_percent", "memory_percent", "mem", "memoryUsage", "mem_usage"])
            disk = _get_first_number(data, ["disk_percent", "disk", "diskUsage", "disk_usage"])
            swap = _get_first_number(data, ["swap_percent", "swap", "swapUsage", "swap_usage"])

            return {
                "ok": True,
                "http_status": http_status,
                "latency_ms": latency_ms,
                "cpu_percent": cpu,
                "mem_percent": mem,
                "disk_percent": disk,
                "swap_percent": swap,
                "raw_json": raw,
                "reason": None,
                "url": url,
            }

        except requests.Timeout:
            # retry on timeout
            last_latency = int((time.perf_counter() - t0) * 1000)
            if attempt < retries:
                continue
            return _fail("timeout", last_latency, url)

        except requests.RequestException:
            # retry on request errors
            last_latency = int((time.perf_counter() - t0) * 1000)
            if attempt < retries:
                continue
            return _fail("request_error", last_latency, url)

        except ValueError:
            # JSON parse error - no retry
            last_latency = int((time.perf_counter() - t0) * 1000)
            return _fail("bad_json", last_latency, url)

    # should never hit
    return _fail("unknown", last_latency, url)


def _fail(reason: str, latency_ms: int | None, url: str):
    return {
        "ok": False,
        "http_status": None,
        "latency_ms": latency_ms,
        "cpu_percent": None,
        "mem_percent": None,
        "disk_percent": None,
        "swap_percent": None,
        "raw_json": None,
        "reason": reason,
        "url": url,
    }


def _get_first_number(data: dict, keys: list[str]):
    """
    Try to find a numeric value in:
    - data[key] as int/float
    - data[key] as dict with fields percent/pct/value
    """
    for k in keys:
        v = data.get(k, None)

        if isinstance(v, (int, float)):
            return float(v)

        if isinstance(v, dict):
            for kk in ("percent", "pct", "value"):
                vv = v.get(kk)
                if isinstance(vv, (int, float)):
                    return float(vv)

    return None
