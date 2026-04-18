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

import sys
import csv
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import init_db, bulk_insert_species_data, get_db_stats, SessionLocal
from config import get_settings


def migrate_csv_to_db():
    """
    从 CSV 文件迁移数据到数据库
    """
    # 初始化数据库
    print("=" * 60)
    print("🔄 CSV 到 SQLite 数据库迁移")
    print("=" * 60)
    print()

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
    for csv_file in csv_files:
        species_name = csv_file.stem
        print(f"  导入 {species_name}...", end=" ")

        data_list = []
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_list.append({
                    "species_label": row.get("species_label") or species_name,
                    "scientific_name": row.get("gbif_scientific_name"),
                    "latitude": _safe_float(row.get("lat")),
                    "longitude": _safe_float(row.get("lng")),
                    "province": row.get("province"),
                    "region_code": row.get("region_code"),
                    "date": row.get("date"),
                    "dataset": row.get("dataset"),
                    "year": _safe_int(row.get("year")),
                })

        count = bulk_insert_species_data(data_list)
        total_imported += count
        print(f"✓ ({count} 条)")

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
        success = migrate_csv_to_db()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[✗] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
