"""问答结果缓存：规范化问题文本 + SHA256 键 + TTL。"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any, Optional

from config import get_settings


def _norm_q(q: str) -> str:
    return " ".join((q or "").strip().split())


class QaCache:
    def __init__(self):
        self._data: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()

    def _key(self, question: str) -> str:
        n = _norm_q(question)
        return hashlib.sha256(n.encode("utf-8")).hexdigest()

    def get(self, question: str) -> Optional[dict[str, Any]]:
        s = get_settings()
        if s.qa_cache_max_entries <= 0:
            return None
        k = self._key(question)
        now = time.time()
        if k not in self._data:
            return None
        ts, payload = self._data[k]
        if now - ts > s.qa_cache_ttl_seconds:
            del self._data[k]
            return None
        self._data.move_to_end(k)
        return payload

    def set(self, question: str, payload: dict[str, Any]) -> None:
        s = get_settings()
        if s.qa_cache_max_entries <= 0:
            return
        k = self._key(question)
        self._data[k] = (time.time(), payload.copy())
        self._data.move_to_end(k)
        while len(self._data) > s.qa_cache_max_entries:
            self._data.popitem(last=False)

    def clear(self):
        self._data.clear()


qa_cache = QaCache()
