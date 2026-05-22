import unittest
import os
import tempfile
import sqlite3
from dump import copy_database
import logging
from io import StringIO
import sys


class TestDump(unittest.TestCase):
    """测试dump.py中的数据库复制功能"""

    def setUp(self):
        """测试前的准备工作，创建临时文件和测试数据库"""
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时源数据库文件
        self.source_db = os.path.join(self.temp_dir.name, "source.db")
        
        # 创建临时目标数据库文件
        self.target_db = os.path.join(self.temp_dir.name, "target.db")
        
        # 创建带有测试数据的源数据库
        self._create_test_database(self.source_db)
        
        # 保存原始的stdout和stderr，用于后续测试
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # 配置日志记录器以捕获警告信息
        self.log_capture = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.logger = logging.getLogger('sqlite_dump')
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        """测试后的清理工作，删除临时文件"""
        # 清理临时目录
        self.temp_dir.cleanup()
        
        # 清理可能创建的日志文件
        for log_file in ['dump.log.txt']:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass
        
        # 恢复原始的stdout和stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # 移除日志处理器
        if self.log_handler in self.logger.handlers:
            self.logger.removeHandler(self.log_handler)
        self.log_capture.close()

    def _create_test_database(self, db_path):
        """创建带有测试数据的SQLite数据库"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建测试表1
        cursor.execute('''
            CREATE TABLE test_table1 (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        ''')
        
        # 插入测试数据
        test_data1 = [
            (1, 'Item 1', 100),
            (2, 'Item 2', 200),
            (3, 'Item 3', 300)
        ]
        cursor.executemany('INSERT INTO test_table1 VALUES (?, ?, ?)', test_data1)
        
        # 创建测试表2
        cursor.execute('''
            CREATE TABLE test_table2 (
                id INTEGER PRIMARY KEY,
                description TEXT
            )
        ''')
        
        # 插入测试数据
        test_data2 = [
            (1, 'Description 1'),
            (2, 'Description 2')
        ]
        cursor.executemany('INSERT INTO test_table2 VALUES (?, ?)', test_data2)
        
        # 提交并关闭连接
        conn.commit()
        conn.close()

    def _get_table_count(self, db_path):
        """获取数据库中的表数量"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _get_record_count(self, db_path, table_name):
        """获取指定表中的记录数量"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def test_copy_database_normal_case(self):
        """测试正常情况下的数据库复制"""
        # 执行复制
        copy_database(self.source_db, self.target_db)
        
        # 验证目标数据库是否存在
        self.assertTrue(os.path.exists(self.target_db))
        
        # 验证表数量是否一致
        source_table_count = self._get_table_count(self.source_db)
        target_table_count = self._get_table_count(self.target_db)
        self.assertEqual(target_table_count, source_table_count)
        
        # 验证记录数量是否一致
        for table_name in ['test_table1', 'test_table2']:
            source_count = self._get_record_count(self.source_db, table_name)
            target_count = self._get_record_count(self.target_db, table_name)
            self.assertEqual(target_count, source_count)

    def test_copy_database_source_not_exists(self):
        """测试源数据库不存在的情况"""
        # 源数据库文件不存在
        non_existent_db = os.path.join(self.temp_dir.name, "non_existent.db")
        
        # 验证是否抛出FileNotFoundError异常
        with self.assertRaises(FileNotFoundError):
            copy_database(non_existent_db, self.target_db)

    def test_copy_database_empty_source(self):
        """测试源数据库为空的情况"""
        # 创建一个空的源数据库
        empty_db = os.path.join(self.temp_dir.name, "empty.db")
        conn = sqlite3.connect(empty_db)
        conn.close()
        
        # 执行复制
        copy_database(empty_db, self.target_db)
        
        # 验证目标数据库是否存在
        self.assertTrue(os.path.exists(self.target_db))
        
        # 验证目标数据库也是空的
        target_table_count = self._get_table_count(self.target_db)
        self.assertEqual(target_table_count, 0)

    def test_copy_database_target_exists(self):
        """测试目标数据库已存在的情况"""
        # 先创建一个已存在的目标数据库
        existing_target = os.path.join(self.temp_dir.name, "existing_target.db")
        conn = sqlite3.connect(existing_target)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE existing_table (id INTEGER)')
        cursor.execute('INSERT INTO existing_table VALUES (1)')
        conn.commit()
        conn.close()
        
        # 清空日志捕获缓冲区
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        # 执行复制操作
        copy_database(self.source_db, existing_target)
        
        # 验证警告信息是否正确输出
        log_content = self.log_capture.getvalue()
        self.assertIn("目标数据库文件", log_content)
        self.assertIn("已存在，取消复制操作", log_content)
        
        # 验证已存在的数据库内容没有被修改
        conn = sqlite3.connect(existing_target)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='existing_table'")
        result = cursor.fetchone()
        self.assertIsNotNone(result, "原有表应该仍然存在")
        cursor.execute("SELECT COUNT(*) FROM existing_table")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "原有表的记录数应该保持不变")
        conn.close()


if __name__ == '__main__':
    unittest.main()