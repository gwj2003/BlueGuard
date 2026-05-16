"""Geocoding service helpers.

This service uses AMap (高德) as the sole geocoding provider.

Set `AMAP_KEY` via environment or `.env` to enable AMap. If `AMAP_KEY` is not configured
the service will return an explicit HTTP error indicating that geocoding is unavailable.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import requests
from fastapi import HTTPException

from config import get_settings


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

        # Only use AMap. If key is not configured, return explicit error.
        if not (hasattr(self, "_amap_key") and self._amap_key):
            raise HTTPException(status_code=503, detail="未配置 AMAP_KEY，无法进行地理编码")

        params = {"address": normalized, "key": self._amap_key, "output": "json", "offset": 0}
        payload = self._request_json("https://restapi.amap.com/v3/geocode/geo", params=params)
        # AMap returns status: '1' for success, '0' for failure
        if not isinstance(payload, dict) or str(payload.get('status')) != '1':
            info = payload.get('info') if isinstance(payload, dict) else None
            infocode = payload.get('infocode') if isinstance(payload, dict) else None
            raise HTTPException(status_code=502, detail=f"AMap 地理编码失败: {info or 'unknown'} ({infocode or ''})")
        geocodes = payload.get("geocodes")
        if not geocodes:
            raise HTTPException(status_code=404, detail="无法找到地址（AMap）")
        first = geocodes[0]
        # AMap 返回 location 字段格式为 "lon,lat"
        loc = first.get("location", "")
        lon_str, lat_str = (loc.split(",") + [""])[:2]
        try:
            lon_v = float(lon_str)
            lat_v = float(lat_str)
        except ValueError:
            raise HTTPException(status_code=502, detail="地理编码返回了无效坐标（AMap）")
        result = {"lat": lat_v, "lon": lon_v, "display_name": first.get("formatted_address", "")}
        self._set_cache(self._forward_cache, normalized, result)
        return result

    def reverse_geocode(self, lat: float, lon: float) -> dict[str, Any]:
        cache_key = f"{lat:.6f},{lon:.6f}"
        cached = self._get_cache(self._reverse_cache, cache_key)
        if cached is not None:
            return cached
        # Only use AMap. If key is not configured, return explicit error.
        if not (hasattr(self, "_amap_key") and self._amap_key):
            raise HTTPException(status_code=503, detail="未配置 AMAP_KEY，无法进行逆向地理编码")

        # AMap expects location as lon,lat
        params = {"location": f"{lon},{lat}", "key": self._amap_key, "output": "json", "extensions": "all"}
        payload = self._request_json("https://restapi.amap.com/v3/geocode/regeo", params=params)
        if not isinstance(payload, dict) or str(payload.get('status')) != '1':
            info = payload.get('info') if isinstance(payload, dict) else None
            infocode = payload.get('infocode') if isinstance(payload, dict) else None
            raise HTTPException(status_code=502, detail=f"AMap 逆向地理编码失败: {info or 'unknown'} ({infocode or ''})")
        regeocode = payload.get("regeocode")
        address = ""
        if regeocode:
            address = regeocode.get("formatted_address", "")
        result = {"address": address}
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

# initialize provider settings from application config
_settings = get_settings()
if getattr(_settings, "amap_key", None):
    # prefer AMap when configured
    geocoding_service._amap_key = _settings.amap_key
    # AMap key configured
