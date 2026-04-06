"""Geocoding service helpers."""

from __future__ import annotations

import threading
import time
from typing import Any

import requests
from fastapi import HTTPException


class GeocodingService:
    def __init__(self, min_interval_seconds: float = 1.0, cache_ttl_seconds: int = 600):
        self._min_interval_seconds = min_interval_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = threading.RLock()
        self._last_called_at = 0.0
        self._session = requests.Session()
        self._headers = {"User-Agent": "aquatic-species-platform"}
        self._forward_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._reverse_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def geocode(self, address: str) -> dict[str, Any]:
        normalized = (address or "").strip()
        if not normalized:
            raise HTTPException(status_code=400, detail="地址不能为空")

        cached = self._get_cache(self._forward_cache, normalized)
        if cached is not None:
            return cached

        payload = self._request_json(
            "https://nominatim.openstreetmap.org/search",
            params={"q": normalized, "format": "json", "limit": 1},
        )
        if not payload:
            raise HTTPException(status_code=404, detail="无法找到地址")

        first = payload[0]
        result = {
            "lat": float(first["lat"]),
            "lon": float(first["lon"]),
            "display_name": first.get("display_name", ""),
        }
        self._set_cache(self._forward_cache, normalized, result)
        return result

    def reverse_geocode(self, lat: float, lon: float) -> dict[str, Any]:
        cache_key = f"{lat:.6f},{lon:.6f}"
        cached = self._get_cache(self._reverse_cache, cache_key)
        if cached is not None:
            return cached

        payload = self._request_json(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
        )
        result = {"address": payload.get("display_name", "")}
        self._set_cache(self._reverse_cache, cache_key, result)
        return result

    def _request_json(self, url: str, *, params: dict[str, Any]) -> Any:
        try:
            with self._lock:
                now = time.monotonic()
                remaining = self._min_interval_seconds - (now - self._last_called_at)
                if remaining > 0:
                    time.sleep(remaining)

                response = self._session.get(url, params=params, headers=self._headers, timeout=15)
                response.raise_for_status()
                self._last_called_at = time.monotonic()

            return response.json()
        except requests.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"地理编码服务响应异常: {exc}") from exc
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=f"地理编码服务请求失败: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"地理编码服务返回了无效数据: {exc}") from exc

    def _get_cache(self, cache: dict[str, tuple[float, dict[str, Any]]], key: str) -> dict[str, Any] | None:
        with self._lock:
            row = cache.get(key)
            if row is None:
                return None
            ts, payload = row
            if time.time() - ts > self._cache_ttl_seconds:
                cache.pop(key, None)
                return None
            return payload.copy()

    def _set_cache(self, cache: dict[str, tuple[float, dict[str, Any]]], key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            cache[key] = (time.time(), payload.copy())


geocoding_service = GeocodingService()
