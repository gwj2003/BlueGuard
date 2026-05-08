#!/usr/bin/env python3
"""
CSV 到 SQLite 数据库迁移脚本

用法：
    python tools/migrate_csv_to_db.py

说明：
    - 自动扫描 backend/data/gbif_results/ 目录中的所有 CSV 文件
    - 将数据导入到 SQLite 数据库
    - 备份原始 CSV 文件到 backup/ 目录
"""

import argparse
import sys
import csv
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import init_db, bulk_insert_species_data, get_db_stats, SessionLocal, engine
from config import get_settings
from models import Base


def reset_database():
    """清空当前 SQLite 数据库中的所有表，并重新创建结构。"""
    print("[0/4] 清空现有数据库...")
    Base.metadata.drop_all(bind=engine)
    init_db()
    print("[0/4] 数据库已清空并重新初始化。")


def migrate_csv_to_db(clear_before_import: bool = False):
    """
    从 CSV 文件迁移数据到数据库
    """
    # 初始化数据库
    print("=" * 60)
    print("🔄 CSV 到 SQLite 数据库迁移")
    print("=" * 60)
    print(f"[配置] 本次是否清库: {'是' if clear_before_import else '否'}")
    print()

    if clear_before_import:
        reset_database()

    print("[1/4] 初始化数据库...")
    init_db()
    print()

    # 获取 GBIF CSV 文件目录
    gbif_dir = get_settings().data_dir / "gbif_results"
    if not gbif_dir.exists():
        print(f"[✗] 错误：GBIF 数据目录不存在: {gbif_dir}")
        return False

    # 找出所有 CSV 文件
    csv_files = sorted(gbif_dir.glob("*.csv"))
    if not csv_files:
        print(f"[✗] 错误：未找到任何 CSV 文件在 {gbif_dir}")
        return False

    print(f"[2/4] 发现 {len(csv_files)} 个物种数据文件:")
    for csv_file in csv_files:
        print(f"  • {csv_file.name}")
    print()

    # 导入数据
    print("[3/4] 导入数据到数据库...")
    total_imported = 0
    # 候选列名映射：支持不同来源 CSV 的多种列名
    FIELD_CANDIDATES = {
        "species_label": ["species_label", "species", "speciesName", "species_label_trimmed"],
        "scientific_name": ["gbif_scientific_name", "scientific_name", "scientificName"],
        "latitude": ["lat", "latitude", "decimalLatitude", "Lat"],
        "longitude": ["lng", "lon", "longitude", "decimalLongitude", "Lon"],
        "province": ["province", "admin1", "state_province", "province_name"],
        "region_code": ["region_code", "region", "region_code"],
        "date": ["date", "eventDate", "occurrenceDate"],
        "dataset": ["dataset", "data_source", "datasetKey"],
        "year": ["year", "Year", "eventYear"],
    }

    CHUNK_SIZE = 5000  # 大文件分批插入以减少内存峰值

    def _get_first(row: dict, candidates: list[str]):
        for c in candidates:
            if c in row and row[c] is not None and str(row[c]).strip() != "":
                return row[c]
        return None

    for csv_file in csv_files:
        species_name = csv_file.stem
        print(f"  导入 {species_name}...", end=" ")

        imported_count = 0
        batch: list[dict] = []
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 兼容不同列名，优先取行内的 species_label，否则用文件名
                sp = _get_first(row, FIELD_CANDIDATES["species_label"]) or species_name
                sci = _get_first(row, FIELD_CANDIDATES["scientific_name"]) or None
                lat_raw = _get_first(row, FIELD_CANDIDATES["latitude"])
                lng_raw = _get_first(row, FIELD_CANDIDATES["longitude"])
                prov = _get_first(row, FIELD_CANDIDATES["province"]) or None
                rcode = _get_first(row, FIELD_CANDIDATES["region_code"]) or None
                date_raw = _get_first(row, FIELD_CANDIDATES["date"]) or None
                ds = _get_first(row, FIELD_CANDIDATES["dataset"]) or None
                year_raw = _get_first(row, FIELD_CANDIDATES["year"]) or None

                # 尝试从 date 中解析 year（若 year 字段缺失）
                year_val = _safe_int(year_raw) if year_raw else None
                if not year_val and date_raw:
                    try:
                        # 支持 YYYY 或 YYYY-MM-DD
                        year_val = int(str(date_raw).strip()[:4])
                    except Exception:
                        year_val = None

                batch.append({
                    "species_label": sp,
                    "scientific_name": sci,
                    "latitude": _safe_float(lat_raw),
                    "longitude": _safe_float(lng_raw),
                    "province": prov,
                    "region_code": rcode,
                    "date": date_raw,
                    "dataset": ds,
                    "year": year_val,
                })

                if len(batch) >= CHUNK_SIZE:
                    cnt = bulk_insert_species_data(batch)
                    imported_count += cnt
                    batch = []

        # 插入剩余批次
        if batch:
            cnt = bulk_insert_species_data(batch)
            imported_count += cnt

        total_imported += imported_count
        print(f"✓ ({imported_count} 条)")

    print()
    print("[4/4] 迁移结果统计...")
    db = SessionLocal()
    try:
        stats = get_db_stats(db)
        print(f"  • 总分布记录数: {stats['total_species_records']}")
        print(f"  • 物种数: {stats['unique_species']}")
        print(f"  • 用户上报记录: {stats['user_records']}")
    finally:
        db.close()

    print()
    print("=" * 60)
    print("✅ 迁移完成！")
    print("=" * 60)
    print()
    print("📊 数据库位置:")
    print(f"   {get_settings().runtime_dir / 'species.db'}")
    print()
    print("💡 后续步骤:")
    print("   1. 不再需要 CSV 文件可以删除或备份")
    print("   2. 修改后端代码使用数据库（已自动配置）")
    print("   3. 启动应用: python -m uvicorn main:app --reload")
    print()

    return True


def prompt_clear_database(default: bool = False) -> bool:
    """在交互式终端中询问是否清空数据库。"""
    default_hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"是否在导入前清空数据库？[{default_hint}] ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes", "是", "1", "true"}:
            return True
        if answer in {"n", "no", "否", "0", "false"}:
            return False
        print("请输入 y / n。")


def _safe_float(value) -> float:
    """安全地转换为浮点数"""
    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> int:
    """安全地转换为整数"""
    try:
        return int(value) if value else None
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="CSV 到 SQLite 数据库迁移")
        parser.add_argument(
            "--prompt-clear",
            action="store_true",
            help="启动后交互询问是否清空数据库（默认行为）",
        )
        parser.add_argument(
            "--clear-db",
            action="store_true",
            help="在导入前清空现有数据库表并重新创建",
        )
        parser.add_argument(
            "--keep-db",
            action="store_true",
            help="明确指定不清空数据库，直接追加导入",
        )
        args = parser.parse_args()

        if args.clear_db and args.keep_db:
            raise ValueError("--clear-db 和 --keep-db 不能同时使用")

        if args.clear_db:
            clear_before_import = True
        elif args.keep_db:
            clear_before_import = False
        elif args.prompt_clear or sys.stdin.isatty():
            clear_before_import = prompt_clear_database(default=False)
        else:
            clear_before_import = False

        success = migrate_csv_to_db(clear_before_import=clear_before_import)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[✗] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
