import os
import logging
import sqlite3
from datetime import datetime
from dump_config import DumpConfig

# 创建logger对象
logger = logging.getLogger('sqlite_dump')


def copy_database(source_path, target_path):
  """复制源数据库到目标数据库，如果目标数据库已存在则不进行复制操作，并生成markdown格式的复制报告"""
  # 记录开始时间
  start_time = datetime.now()
  logger.warning(f"复制数据库开始: {source_path} -> {target_path} [{start_time.strftime('%Y-%m-%d %H:%M:%S')}]")
  
  # 用于存储表复制信息的列表
  table_results = []
  
  # 初始化总体结果状态
  overall_status = "成功"
  error_message = None
  table_count = 0
  total_records = 0
  
  if os.path.exists(target_path):
    logger.warning(f"目标数据库文件 '{target_path}' 已存在，取消复制操作。若要覆盖现有文件，请先手动删除。")
    # 即使取消操作，也生成报告
    overall_status = "取消"
    error_message = f"目标数据库文件 '{target_path}' 已存在"
  else:
    try:
      # 检查源数据库是否存在
      if not os.path.exists(source_path):
        error_msg = f"源数据库文件不存在: {source_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

      # 连接源数据库
      source_conn = sqlite3.connect(source_path)
      source_cursor = source_conn.cursor()
      logger.info(f"成功连接源数据库: {source_path}")

      # 连接目标数据库（如果不存在则创建）
      target_conn = sqlite3.connect(target_path)
      target_cursor = target_conn.cursor()
      logger.info(f"成功连接/创建目标数据库: {target_path}")

      # 获取源数据库中所有表
      source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
      tables = source_cursor.fetchall()

      if not tables:
        logger.info("源数据库中没有找到任何表")
      else:
        # 遍历并复制每个表
        for table in tables:
          table_name = table[0]
          table_status = "成功"
          record_count = 0
          table_error = None
          
          # 跳过系统表
          if table_name.startswith('sqlite_'):
            table_results.append({
              "name": table_name,
              "status": "跳过",
              "reason": "系统表",
              "records": 0
            })
            continue

          table_count += 1
          try:
            # 创建表结构
            source_cursor.execute(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_sql = source_cursor.fetchone()[0]
            target_cursor.execute(create_sql)

            # 复制数据
            source_cursor.execute(f"SELECT * FROM {table_name};")
            rows = source_cursor.fetchall()

            if rows:
              # 获取列数
              col_count = len(rows[0])
              placeholders = ', '.join(['?'] * col_count)

              target_cursor.executemany(
                  f"INSERT INTO {table_name} VALUES ({placeholders});",
                  rows
              )
              record_count = len(rows)
              total_records += record_count
              logger.info(f"已复制表 {table_name} 的 {record_count} 条记录")
            else:
              logger.info(f"表 {table_name} 没有记录需要复制")
              table_status = "成功（无数据）"
          except Exception as e:
            table_status = "失败"
            table_error = str(e)
            logger.error(f"复制表 {table_name} 时出错: {table_error}")
          
          # 记录表复制结果
          table_results.append({
            "name": table_name,
            "status": table_status,
            "reason": table_error if table_error else "",
            "records": record_count
          })

        # 提交事务
        target_conn.commit()
        logger.info(f"\n复制完成！共处理 {table_count} 个表，总计 {total_records} 条记录")
        logger.info(f"成功将数据从 {source_path} 复制到 {target_path}")

      # 如果有表复制失败，更新总体状态
      failed_tables = [t for t in table_results if t["status"] == "失败"]
      if failed_tables:
        overall_status = "部分成功"

    except Exception as e:
      error_msg = f"复制过程中出错: {str(e)}"
      logger.error(error_msg)
      if 'target_conn' in locals():
        target_conn.rollback()
      overall_status = "失败"
      error_message = error_msg
    
    finally:
      # 关闭连接
      if 'source_conn' in locals():
        source_conn.close()
        logger.info("源数据库连接已关闭")
      if 'target_conn' in locals():
        target_conn.close()
        logger.info("目标数据库连接已关闭")
  
  # 计算运行时间
  end_time = datetime.now()
  execution_time = end_time - start_time
  
  # 修改日志输出，添加运行时间信息
  logger.warning(f"复制数据库完成({execution_time.total_seconds():.2f}秒): {source_path} -> {target_path}")
  
  # 生成markdown格式的报告
  generate_report(
    source_path=source_path,
    target_path=target_path,
    start_time=start_time,
    end_time=end_time,
    execution_time=execution_time,
    overall_status=overall_status,
    error_message=error_message,
    table_results=table_results,
    total_tables=table_count,
    total_records=total_records
  )


def generate_report(source_path, target_path, start_time, end_time, execution_time, 
                   overall_status, error_message, table_results, total_tables, total_records):
  """生成markdown格式的复制报告"""
  try:
    with open("dump.result.md", "w", encoding="utf-8") as md_file:
      # 写入标题和基本信息
      md_file.write(f"# 数据库复制结果\n\n")
      md_file.write(f"生成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
      md_file.write(f"## 基本信息\n\n")
      md_file.write(f"| 项目 | 信息 |\n")
      md_file.write(f"|------|------|\n")
      md_file.write(f"| 源数据库 | `{source_path}` |\n")
      md_file.write(f"| 目标数据库 | `{target_path}` |\n")
      md_file.write(f"| 开始时间 | {start_time.strftime('%Y-%m-%d %H:%M:%S')} |\n")
      md_file.write(f"| 结束时间 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |\n")
      md_file.write(f"| 总耗时 | {execution_time.total_seconds():.2f} 秒 |\n\n")
      
      # 写入总体结果
      md_file.write(f"## 总体结果\n\n")
      status_emoji = {
        "成功": "✅",
        "部分成功": "⚠️", 
        "失败": "❌",
        "取消": "⏸️"
      }.get(overall_status, "")
      
      md_file.write(f"{status_emoji} **{overall_status}**\n\n")
      if error_message:
        md_file.write(f"**错误信息**: {error_message}\n\n")
      
      # 写入表复制明细表格
      md_file.write("## 表复制明细\n\n")
      md_file.write("| 表名 | 状态 | 记录数 | 备注 |\n")
      md_file.write("|------|------|-------|------|\n")
      
      # 填充表格数据
      for table in table_results:
        status_text = table["status"]
        if status_text == "成功":
          status_text = "✅ 成功"
        elif status_text == "成功（无数据）":
          status_text = "✅ 成功（无数据）"
        elif status_text == "失败":
          status_text = "❌ 失败"
        elif status_text == "跳过":
          status_text = "⏸️ 跳过"
        
        reason = table["reason"] if table["reason"] else "-"
        md_file.write(f"| {table['name']} | {status_text} | {table['records']} | {reason} |\n")
      
      # 添加总结信息
      md_file.write(f"\n## 复制总结\n\n")
      md_file.write(f"- 总表数: {total_tables}\n")
      md_file.write(f"- 总记录数: {total_records}\n")
      
      # 统计各状态的表数量
      success_tables = sum(1 for t in table_results if t["status"] in ["成功", "成功（无数据）"])
      failed_tables = sum(1 for t in table_results if t["status"] == "失败")
      skipped_tables = sum(1 for t in table_results if t["status"] == "跳过")
      
      md_file.write(f"- 成功表数: {success_tables}\n")
      md_file.write(f"- 失败表数: {failed_tables}\n")
      md_file.write(f"- 跳过表数: {skipped_tables}\n")
    
    logger.info(f"复制报告已保存到 dump.result.md")
  except Exception as e:
    logger.error(f"生成报告时出错: {str(e)}")


# 使用示例
if __name__ == "__main__":
  try:
    # 使用DumpConfig类加载配置
    config = DumpConfig.from_json_file()

    # 主动验证配置
    config.validate()

    # 执行复制 - 直接访问类的属性
    copy_database(config.source_database, config.target_database)
  except Exception as e:
    # 确保错误信息被记录到日志
    logger.error(f"操作失败: {str(e)}")