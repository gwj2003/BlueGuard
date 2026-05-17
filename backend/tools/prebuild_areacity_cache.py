#!/usr/bin/env python3
"""预生成 AreaCity_ok_geo 的按级别 GeoJSON 磁盘缓存。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from services.analytics import _build_areacity_csv_geojson


def main() -> int:
    parser = argparse.ArgumentParser(description="预生成 AreaCity_ok_geo 的行政区缓存")
    parser.add_argument(
        "--levels",
        default="city,district",
        help="要预生成的级别，逗号分隔，默认 city,district",
    )
    args = parser.parse_args()

    levels = tuple(
        level.strip()
        for level in str(args.levels).split(",")
        if level.strip()
    )
    if not levels:
        print("未指定有效级别")
        return 1

    print(f"开始预生成缓存: {', '.join(levels)}")
    result: dict[str, bool] = {}
    for level in levels:
        payload = _build_areacity_csv_geojson(level)
        result[level] = payload is not None
        print(f"  {level}: {'OK' if result[level] else 'FAILED'}")
    return 0 if all(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
