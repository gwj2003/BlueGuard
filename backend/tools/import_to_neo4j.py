import os
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase

# ================= 1. 配置区域 =================
# Neo4j 连接信息 (请根据你的实际情况修改)：
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "******"  # 👈 记得确认密码

# CSV 数据目录
DATA_DIR = str(Path(__file__).resolve().parent.parent / "data" / "triplets")

# ================= 2. 核心逻辑：关系映射 =================
# 这个字典告诉程序：如果关系是 X，那么目标节点 Entity2 应该是什么标签 (Label)
# Entity1 永远是 "Species" (因为是星型拓扑)
REL_TO_LABEL_MAP = {
    "HAS_ALIAS": "Species",  # 别名也是一种物种名
    "BELONGS_TO": "Taxonomy",  # 属于 -> 分类单元
    "NATIVE_TO": "Location",  # 原产于 -> 地点
    "INVADES": "Location",  # 入侵了 -> 地点
    "CAUSES": "Impact",  # 造成 -> 危害
    "SUPPRESSED_BY": "Control"  # 被防治 -> 措施
}


# ================= 3. 功能函数 =================

def parse_properties(prop_str):
    """
    把 CSV 里的 "time=1981;type=农业" 字符串解析成 Python 字典
    """
    if pd.isna(prop_str) or prop_str == "null" or not prop_str:
        return {}

    props = {}
    # 先按分号拆分多个属性
    items = str(prop_str).split(';')
    for item in items:
        if '=' in item:
            key, value = item.split('=', 1)
            props[key.strip()] = value.strip()
    return props


def import_csv_to_graph(driver, filepath):
    """读取单个 CSV 并写入 Neo4j (增强版：自动修复表头问题)"""
    filename = os.path.basename(filepath)

    try:
        # 🌟 修复 1: 使用 'utf-8-sig' 编码，它可以自动去除 BOM 头 (\ufeff)
        # 🌟 修复 2: on_bad_lines='skip' 跳过格式错误的坏行
        df = pd.read_csv(filepath, encoding='utf-8-sig', on_bad_lines='skip')

        # 🌟 修复 3: 强制去除列名的前后空格 (防止 'Entity1 ' 这种情况)
        df.columns = [c.strip() for c in df.columns]

        # 🔍 调试信息：如果列名不对，打印出来让我们看到
        if 'Entity1' not in df.columns:
            print(f"  ⚠️ 跳过 {filename}: 表头格式错误。实际表头是: {df.columns.tolist()}")
            return

        print(f"📄 正在处理: {filename} ({len(df)} 条数据)")

        with driver.session() as session:
            for index, row in df.iterrows():
                try:
                    # 🌟 修复 4: 增加安全性检查，防止空值报错
                    if pd.isna(row['Entity1']) or pd.isna(row['Entity2']):
                        continue

                    e1_name = str(row['Entity1']).strip()
                    rel_type = str(row['Relationship']).strip()
                    e2_name = str(row['Entity2']).strip()
                    raw_props = row['Property']

                    # 1. 解析属性
                    rel_props = parse_properties(raw_props)

                    # 2. 确定目标节点的 Label
                    target_label = REL_TO_LABEL_MAP.get(rel_type, "Entity")

                    # 3. 构建 Cypher
                    cypher = f"""
                    MERGE (s:Species {{name: $e1_name}})
                    MERGE (t:{target_label} {{name: $e2_name}})
                    MERGE (s)-[r:{rel_type}]->(t)
                    SET r += $props
                    """

                    session.run(cypher, e1_name=e1_name, e2_name=e2_name, props=rel_props)
                except Exception as inner_e:
                    # 某一行出错不影响整个文件
                    print(f"    ⚠️ 第 {index + 1} 行插入失败: {inner_e}")

        print(f"  ✅ {filename} 导入完成！")

    except Exception as e:
        print(f"  ❌ 读取文件 {filename} 失败: {e}")


# ================= 4. 主程序 =================

def main():
    # 1. 检查数据目录
    if not os.path.exists(DATA_DIR):
        print(f"❌ 目录不存在: {DATA_DIR}。请先运行 extract_triplets.py")
        return

    # 2. 连接数据库
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # 测试连接
        driver.verify_connectivity()
        print("🔌 Neo4j 连接成功！准备开始导入...")
    except Exception as e:
        print(f"❌ 无法连接 Neo4j: {e}")
        return

    # 3. (可选) 清空旧数据 - 开发阶段建议打开，防止数据重复堆积
    # input("⚠️ 警告: 即将清空数据库现有数据。按回车继续，按 Ctrl+C 取消...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("🧹 旧数据已清空。")

    # 4. 遍历 CSV 文件导入
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    if not csv_files:
        print("⚠️ 没找到 CSV 文件。")
        return

    for csv_file in csv_files:
        full_path = os.path.join(DATA_DIR, csv_file)
        import_csv_to_graph(driver, full_path)

    driver.close()
    print("\n🎉 全部导入完成！现在去运行 直接调用api回答代码中的问题.py 试试吧！")


if __name__ == "__main__":
    main()