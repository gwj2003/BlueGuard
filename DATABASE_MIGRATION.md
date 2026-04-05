# 📚 SQLite 数据库迁移指南

**版本**: 1.0
**更新**: 2024-04-05
**目的**: 将 CSV 数据迁移到 SQLite 数据库，支持多用户并发读写

---

## 🎯 迁移目标

| 指标 | 改进 |
|------|------|
| **数据存储** | CSV 文件 → SQLite 数据库 |
| **查询性能** | 全表扫描 → 索引查询（提升 10-100 倍） |
| **并发支持** | 单点写入 → 多点读取 + 单点写入 |
| **数据一致性** | 手动管理 → 自动事务管理 |
| **数据量** | 福寿螺275条 → 全8物种 ~600K条 |

---

## 📋 迁移步骤

### 第一步：安装新的依赖

```bash
cd backend
pip install -r requirements.txt
```

**新增依赖**：
- `sqlalchemy==2.0.23` - ORM 框架
- `alembic==1.12.1` - 数据库迁移管理

---

### 第二步：运行迁移脚本

```bash
cd backend
python migrate_csv_to_db.py
```

**输出示例**：
```
============================================================
🔄 CSV 到 SQLite 数据库迁移
============================================================

[1/4] 初始化数据库...
✓ 数据库初始化完成: sqlite:///data/species.db

[2/4] 发现 8 个物种数据文件:
  • 大鳄龟.csv
  • 福寿螺.csv
  • 红耳彩龟.csv
  • 美洲牛蛙.csv
  • 豹纹翼甲鲶.csv
  • 非洲大蜗牛.csv
  • 鳄雀鳝.csv
  • 齐氏罗非鱼.csv

[3/4] 导入数据到数据库...
  导入 大鳄龟... ✓ (1 条)
  导入 福寿螺... ✓ (274 条)
  导入 红耳彩龟... ✓ (8910 条)
  导入 美洲牛蛙... ✓ (731 条)
  导入 豹纹翼甲鲶... ✓ (273 条)
  导入 非洲大蜗牛... ✓ (224 条)
  导入 鳄雀鳝... ✓ (34 条)
  导入 齐氏罗非鱼... ✓ (2760 条)

[4/4] 迁移结果统计...
  • 总分布记录数: 13207
  • 物种数: 8
  • 用户上报记录: 0

============================================================
✅ 迁移完成！
============================================================

📊 数据库位置:
   d:\Users\44574\Desktop\BlueGuard\backend\data\species.db

💡 后续步骤:
   1. 不再需要 CSV 文件可以删除或备份
   2. 修改后端代码使用数据库（已自动配置）
   3. 启动应用: python -m uvicorn main:app --reload
```

---

### 第三步：备份 CSV 文件（可选）

迁移成功后，CSV 文件不再使用，可以备份或删除：

```bash
# 备份 CSV 文件
mkdir -p backup/gbif_results_backup_$(date +%Y%m%d)
cp backend/data/gbif_results/*.csv backup/gbif_results_backup_$(date +%Y%m%d)/

# 或者直接删除（若确认不需要）
# rm backend/data/gbif_results/*.csv
```

---

### 第四步：启动应用

应用会自动使用数据库：

```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```

---

## 🏗️ 数据库架构

### 表结构

#### `species_distribution` - 物种分布数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| species_label | String(100) | 物种名称（索引） |
| scientific_name | String(255) | 学名 |
| latitude | Float | 纬度 |
| longitude | Float | 经度 |
| province | String(50) | 省份 |
| region_code | String(10) | 区域代码 |
| date | DateTime | 记录日期 |
| dataset | String(255) | 数据集名称 |
| year | Integer | 年份 |
| created_at | DateTime | 创建时间 |

**索引**：
- `species_label` - 用于快速查询物种

#### `location_records` - 用户上报记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| species | String(100) | 物种名称（索引） |
| latitude | Float | 纬度 |
| longitude | Float | 经度 |
| location_name | String(255) | 位置名称 |
| date | String(10) | 日期 (YYYY-MM-DD) |
| timestamp | DateTime | 确切时间戳 |

**索引**：
- `species` - 用于按物种查询上报记录

---

## 🔒 并发和锁定策略

### 读取操作（R）- 并发无限制 ✓

```python
# 多用户可同时读取物种列表、位置数据
locations = get_locations_by_species(db, species)  # 无锁
```

### 写入操作（W）- 串行化处理

```python
# 使用线程锁确保数据一致性
with get_write_lock():
    add_location_record(db, species, lat, lon, location_name)
```

**原因**：SQLite 的 WAL（Write-Ahead Logging）模式支持分离的读写，但写操作仍需序列化。

---

## 📊 性能对比

| 操作 | CSV | SQLite | 提升 |
|------|-----|--------|------|
| 获取物种列表 | O(n) 扫描 | O(n) 计数查询 | 相同，但支持缓存 |
| 获取某物种位置 | O(n) 全扫描 | O(log n) 索引查询 | ⬆️ 10-100 倍 |
| 新增记录 | 追加写 | 事务写 | ⬆️ 更安全 |
| 并发读 | 无冲突 | 无冲突 | ✓ 相同 |
| 并发写 | 损坏风险 | 安全 | ⬆️ 更安全 |

---

## 🔧 数据库管理

### 查看数据库统计信息

```bash
# 通过 API 健康检查
curl http://localhost:8000/api/health | jq '.database'

# 输出示例：
# {
#   "total_species_records": 13207,
#   "unique_species": 8,
#   "user_records": 125
# }
```

### 直接访问数据库（SQLite CLI）

```bash
cd backend/data
sqlite3 species.db

# SQLite 命令行示例
.tables                                    # 列出所有表
.schema species_distribution               # 查看表结构
SELECT COUNT(*) FROM species_distribution; # 统计分布记录
SELECT DISTINCT species_label FROM species_distribution; # 查看物种列表
```

### 导出数据为 CSV

```bash
# 使用 SQLite 命令行导出
sqlite3 backend/data/species.db \
  ".mode csv" \
  "SELECT * FROM species_distribution" > export_distribution.csv

sqlite3 backend/data/species.db \
  ".mode csv" \
  "SELECT * FROM location_records" > export_records.csv
```

---

## ⚠️ 注意事项

### 1️⃣ SQLite 并发限制

**特性**：SQLite 在单文件模式下，同时只能有一个写入者

**对策**：
- 系统自动使用线程锁序列化写操作
- 读操作可完全并发，不易受影响
- 如需更好的并发，可迁移到 PostgreSQL

### 2️⃣ 数据库文件位置

```
backend/data/species.db  （~5-10 MB）
```

**备份建议**：定期备份此文件

```bash
cp backend/data/species.db backup/species_db_$(date +%Y%m%d_%H%M%S).db
```

### 3️⃣ 降级方案

如遇到 SQLite 问题，可临时回到 CSV 模式：

```python
# 在 main.py 中修改
# 注释掉 init_db() 的调用
# 恢复使用 _get_locations_list() 的 CSV 实现
```

---

## 🆘 故障排除

### 问题 1：迁移脚本找不到 CSV 文件

```
[✗] 错误：未找到任何 CSV 文件在 D:\...\gbif_results
```

**解决**：确认 CSV 文件位置正确

```bash
ls backend/data/gbif_results/*.csv  # 应显示 8 个文件
```

### 问题 2：导入过程中出错

```
Error inserting data: ...
```

**解决**：检查磁盘空间和权限

```bash
df -h                           # 检查磁盘空间
ls -la backend/data/            # 检查权限
# 删除 species.db 后重试迁移
rm backend/data/species.db
python migrate_csv_to_db.py
```

### 问题 3：应用启动报错 "No module named 'sqlalchemy'"

```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**解决**：重新安装依赖

```bash
pip install -r requirements.txt --force-reinstall
python migrate_csv_to_db.py
```

---

## 📈 未来扩展

### 可选升级方向

| 方案 | 优点 | 缺点 | 难度 |
|------|------|------|------|
| **PostgreSQL** | 更好的并发、备份 | 需要数据库服务 | 中等 |
| **MongoDB** | 灵活的文档结构 | 更高的内存占用 | 中等 |
| **Redis** | 极快的读取 | 需要持久化配置 | 简单 |

---

## ✅ 迁移检查清单

- [ ] 已安装新的依赖（sqlalchemy, alembic）
- [ ] 已运行迁移脚本 `python migrate_csv_to_db.py`
- [ ] 已备份原始 CSV 文件（可选）
- [ ] 已验证应用正常启动
- [ ] 已测试各 API 端点工作正常
- [ ] 已验证前端地图显示正确
- [ ] 已测试用户数据上报功能
- [ ] 已记录数据库位置用于备份

---

## 📞 支持

如有问题或建议，请：
- 📧 查看项目文档
- 🐛 提交问题报告
- 💬 讨论改进方案

---

**迁移完成后享受更好的性能和数据安全性！** 🎉
