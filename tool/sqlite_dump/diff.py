import hashlib
import logging
import sqlite3  # 添加缺失的sqlite3模块导入
from typing import List
from datetime import datetime

from diff_config import DiffConfig

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('diff.log.txt', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def get_db_fingerprint(db_path: str) -> str:
  """生成数据库的“指纹”（结构+数据的MD5哈希）"""
  try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    fingerprint = b""

    # 读取并排序所有表名（排除系统表）
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    # 拼接表结构SQL到指纹
    for table in tables:
      cursor.execute(
          f"SELECT sql FROM sqlite_master WHERE name='{table}' AND type='table';")
      create_sql = cursor.fetchone()[0].strip() + "\n"
      fingerprint += create_sql.encode("utf-8")

      # 拼接表数据到指纹（按主键排序）
      cursor.execute(f"PRAGMA table_info({table});")
      columns = [row[1] for row in cursor.fetchall()]
      pk = "id" if "id" in columns else columns[0] if columns else ""  # 获取排序字段

      if pk:
        cursor.execute(f"SELECT * FROM {table} ORDER BY {pk};")
        for row in cursor.fetchall():
          row_str = "\t".join(str(col) for col in row) + "\n"
          fingerprint += row_str.encode("utf-8")

    conn.close()
    return hashlib.md5(fingerprint).hexdigest()
  except Exception as e:
    logging.error(f"生成数据库{db_path}指纹时出错: {str(e)}")
    raise


def get_table_row_count(conn: sqlite3.Connection, table: str) -> int:
  """获取表的行数"""
  try:
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    return cursor.fetchone()[0]
  except Exception as e:
    logging.warning(f"获取表{table}行数时出错: {str(e)}")
    return -1


def get_table_fingerprint(conn: sqlite3.Connection, table: str) -> str:
  """生成单个表的指纹"""
  try:
    cursor = conn.cursor()
    # 获取表结构
    cursor.execute(
        f"SELECT sql FROM sqlite_master WHERE name='{table}' AND type='table';")
    create_sql = cursor.fetchone()[0].strip() + "\n"

    # 获取表数据
    cursor.execute(f"PRAGMA table_info({table});")
    columns = [row[1] for row in cursor.fetchall()]
    pk = "id" if "id" in columns else columns[0] if columns else ""

    data_str = ""
    if pk:
      cursor.execute(f"SELECT * FROM {table} ORDER BY {pk};")
      data_str = "\n".join("\t".join(str(col) for col in row)
                           for row in cursor.fetchall())

    return hashlib.md5((create_sql + data_str).encode()).hexdigest()
  except Exception as e:
    logging.error(f"生成表{table}指纹时出错: {str(e)}")
    raise


def get_all_tables(conn: sqlite3.Connection) -> List[str]:
  """获取数据库中所有非系统表"""
  cursor = conn.cursor()
  cursor.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
  return [row[0] for row in cursor.fetchall()]


# 修改compare_databases函数，使其输出markdown表格到文件
def compare_databases(db1_path: str, db2_path: str) -> None:
  """对比两个SQLite数据库，结果输出为markdown表格到diff.result.md文件"""
  try:
    logging.info("开始对比数据库...")
    logging.info(f"数据库1: {db1_path}")
    logging.info(f"数据库2: {db2_path}")

    # 收集表的对比信息
    table_comparisons = []
    
    logging.info("开始定位差异表...")

    # 连接两个数据库
    conn1 = sqlite3.connect(db1_path)
    conn2 = sqlite3.connect(db2_path)

    # 获取所有表
    tables1 = get_all_tables(conn1)
    tables2 = get_all_tables(conn2)
    all_tables = set(tables1 + tables2)

    # 逐个表对比
    for table in sorted(all_tables):
      if table not in tables1:
        logging.warning(f"- 表 {table}: 仅存在于数据库2")
        table_comparisons.append({
            "table_name": table,
            "db1_exists": False,
            "db2_exists": True,
            "db1_rows": 0,
            "db2_rows": 0,
            "status": "仅存在于数据库2"
        })
      elif table not in tables2:
        logging.warning(f"- 表 {table}: 仅存在于数据库1")
        table_comparisons.append({
            "table_name": table,
            "db1_exists": True,
            "db2_exists": False,
            "db1_rows": get_table_row_count(conn1, table),
            "db2_rows": 0,
            "status": "仅存在于数据库1"
        })
      else:
        # 对比表指纹
        t1_fp = get_table_fingerprint(conn1, table)
        t2_fp = get_table_fingerprint(conn2, table)

        # 获取行数
        count1 = get_table_row_count(conn1, table)
        count2 = get_table_row_count(conn2, table)
        
        if t1_fp != t2_fp:
          logging.warning(f"- 表 {table}: 结构或数据存在差异")
          logging.warning(f"  - 数据库1中表{table}的行数: {count1}")
          logging.warning(f"  - 数据库2中表{table}的行数: {count2}")
          status = "结构或数据存在差异"
        else:
          status = "相同"
          logging.info(f"- 表 {table}: 相同")
        
        table_comparisons.append({
            "table_name": table,
            "db1_exists": True,
            "db2_exists": True,
            "db1_rows": count1,
            "db2_rows": count2,
            "status": status
        })

    conn1.close()
    conn2.close()
    logging.info("差异表定位完成")
    
    # 写入markdown结果文件
    with open("diff.result.md", "w", encoding="utf-8") as md_file:
      # 写入标题和基本信息
      md_file.write(f"# 数据库对比结果\n\n")
      md_file.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
      md_file.write(f"对比数据库: `{db1_path}` 和 `{db2_path}`\n\n")
      md_file.write(f"## 总体结果\n\n")
      
      # 添加总结信息
      total_tables = len(table_comparisons)
      identical_tables = sum(1 for comp in table_comparisons if comp["status"] == "相同")
      different_tables = total_tables - identical_tables

      if different_tables > 0:
        md_file.write(f"❌ **两个数据库存在差异**\n\n")
      else:
        md_file.write(f"✅ **两个数据库完全相同**\n\n")
      
      # 写入表对比明细表格
      md_file.write("## 表对比明细\n\n")
      md_file.write("| 表名 | 数据库1中存在 | 数据库2中存在 | 数据库1行数 | 数据库2行数 | 状态 |\n")
      md_file.write("|------|------------|------------|----------|----------|------|\n")
      
      # 填充表格数据
      for comp in table_comparisons:
        db1_exists = "✓" if comp["db1_exists"] else "✗"
        db2_exists = "✓" if comp["db2_exists"] else "✗"
        
        # 根据状态添加颜色标记
        status_text = comp["status"]
        if status_text == "相同":
          status_text = "✅ 相同"
        elif status_text == "结构或数据存在差异":
          status_text = "❌ 结构或数据存在差异"
        elif status_text == "仅存在于数据库1":
          status_text = "⚠️ 仅存在于数据库1"
        elif status_text == "仅存在于数据库2":
          status_text = "⚠️ 仅存在于数据库2"
        
        md_file.write(f"| {comp['table_name']} | {db1_exists} | {db2_exists} | {comp['db1_rows']} | {comp['db2_rows']} | {status_text} |\n")
      
      md_file.write(f"\n## 对比总结\n\n")
      md_file.write(f"- 总表数: {total_tables}\n")
      md_file.write(f"- 相同表数: {identical_tables}\n")
      md_file.write(f"- 不同表数: {different_tables}\n")
      
      if different_tables == 0:
        md_file.write(f"- 两个数据库完全相同!\n")
        
    logging.info(f"对比结果已保存到 diff.result.md")

  except Exception as e:
    logging.error(f"数据库对比过程中发生错误: {str(e)}")
    raise


if __name__ == "__main__":
  try:
    # 从配置文件加载配置
    config = DiffConfig.from_json_file()
    config.validate()
    logging.info(f"加载配置成功: 源数据库={config.source_database}, 目标数据库={config.target_database}")
    
    # 使用配置的数据库路径进行对比
    compare_databases(config.source_database, config.target_database)
  except Exception as e:
    logging.error(f"配置加载或数据库对比失败: {str(e)}")