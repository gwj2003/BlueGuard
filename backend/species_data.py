"""GBIF CSV 按路径+mtime 缓存；管理接口可清空。"""
from __future__ import annotations

from functools import lru_cache
import os
from typing import Optional

import pandas as pd


@lru_cache(maxsize=128)
def load_species_data_cached(path_and_mtime: tuple) -> Optional[pd.DataFrame]:
    path, _mtime = path_and_mtime
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def load_csv_for_gbif_file(gbif_path: str):
    if not os.path.exists(gbif_path):
        return None
    mtime = int(os.path.getmtime(gbif_path))
    return load_species_data_cached((gbif_path, mtime))


def clear_csv_cache():
    load_species_data_cached.cache_clear()
