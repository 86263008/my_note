import unittest
import sqlite3
import os
import tempfile
from unittest.mock import patch, mock_open

# 导入被测试的模块
from diff import (
    get_db_fingerprint,
    get_table_row_count,
    get_table_fingerprint,
    get_all_tables,
    compare_databases
)


class TestSqliteDiff(unittest.TestCase):

  def setUp(self):
    # 创建临时数据库文件
    self.db1_fd, self.db1_path = tempfile.mkstemp(suffix='.sqlite')
    self.db2_fd, self.db2_path = tempfile.mkstemp(suffix='.sqlite')
    self.db3_fd, self.db3_path = tempfile.mkstemp(suffix='.sqlite')

    # 创建测试数据
    self._create_test_database(self.db1_path)
    self._create_test_database(self.db2_path)  # 与db1相同的数据库
    self._create_different_database(self.db3_path)  # 与db1不同的数据库

  def tearDown(self):
    # 关闭并删除临时文件
    os.close(self.db1_fd)
    os.close(self.db2_fd)
    os.close(self.db3_fd)
    os.unlink(self.db1_path)
    os.unlink(self.db2_path)
    os.unlink(self.db3_path)

    # 删除测试生成的结果文件
    if os.path.exists('diff.result.md'):
      os.unlink('diff.result.md')

  def _create_test_database(self, db_path):
    # 创建一个简单的测试数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表
    cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        ''')

    cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL
            )
        ''')

    # 插入数据
    cursor.executemany(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
    )

    cursor.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        [("Product 1", 10.99), ("Product 2", 20.99)]
    )

    conn.commit()
    conn.close()

  def _create_different_database(self, db_path):
    # 创建一个与测试数据库不同的数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表（有一个不同的表名和结构）
    cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                email TEXT
            )
        ''')

    cursor.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total REAL
            )
        ''')

    # 插入数据（部分不同）
    cursor.executemany(
        "INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
        [("Alice", 30, "alice@example.com"), ("Bob", 26, "bob@example.com")]
    )

    cursor.executemany(
        "INSERT INTO orders (user_id, total) VALUES (?, ?)",
        [(1, 100.0), (2, 200.0)]
    )

    conn.commit()
    conn.close()

  def test_get_db_fingerprint(self):
    # 测试相同数据库生成相同指纹
    fp1 = get_db_fingerprint(self.db1_path)
    fp2 = get_db_fingerprint(self.db2_path)
    self.assertEqual(fp1, fp2)

    # 测试不同数据库生成不同指纹
    fp3 = get_db_fingerprint(self.db3_path)
    self.assertNotEqual(fp1, fp3)

  def test_get_table_row_count(self):
    # 测试获取表行数
    conn = sqlite3.connect(self.db1_path)
    try:
      self.assertEqual(get_table_row_count(conn, 'users'), 3)
      self.assertEqual(get_table_row_count(conn, 'products'), 2)
      # 测试不存在的表
      self.assertEqual(get_table_row_count(conn, 'non_existent_table'), -1)
    finally:
      conn.close()

  def test_get_table_fingerprint(self):
    # 测试相同表生成相同指纹
    conn1 = sqlite3.connect(self.db1_path)
    conn2 = sqlite3.connect(self.db2_path)
    try:
      fp1 = get_table_fingerprint(conn1, 'users')
      fp2 = get_table_fingerprint(conn2, 'users')
      self.assertEqual(fp1, fp2)

      # 测试不同表生成不同指纹
      fp3 = get_table_fingerprint(conn1, 'products')
      self.assertNotEqual(fp1, fp3)
    finally:
      conn1.close()
      conn2.close()

  def test_get_all_tables(self):
    # 测试获取所有非系统表
    conn = sqlite3.connect(self.db1_path)
    try:
      tables = get_all_tables(conn)
      self.assertEqual(len(tables), 2)
      self.assertIn('users', tables)
      self.assertIn('products', tables)
    finally:
      conn.close()

  @patch('builtins.open', new_callable=mock_open)
  def test_compare_databases_identical(self, mock_file):
    # 测试对比相同的数据库
    compare_databases(self.db1_path, self.db2_path)

    # 验证是否创建了结果文件
    mock_file.assert_called_once_with('diff.result.md', 'w', encoding='utf-8')

    # 验证写入的内容包含预期信息
    handle = mock_file()
    written_content = ''.join(call[0][0]
                              for call in handle.write.call_args_list)
    self.assertIn('两个数据库完全相同', written_content)

  @patch('builtins.open', new_callable=mock_open)
  def test_compare_databases_different(self, mock_file):
    # 测试对比不同的数据库
    compare_databases(self.db1_path, self.db3_path)

    # 验证是否创建了结果文件
    mock_file.assert_called_once_with('diff.result.md', 'w', encoding='utf-8')

    # 验证写入的内容包含预期信息
    handle = mock_file()
    written_content = ''.join(call[0][0]
                              for call in handle.write.call_args_list)
    self.assertIn('两个数据库存在差异', written_content)
    self.assertIn('表对比明细', written_content)


if __name__ == '__main__':
  unittest.main()
