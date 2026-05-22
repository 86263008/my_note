import os
import tempfile
import unittest
import sqlite3
import json
from diff_config import DiffConfig


class TestDiffConfig(unittest.TestCase):
  """测试DiffConfig类的功能"""

  def setUp(self):
    """测试前的准备工作，创建临时文件"""
    # 创建临时配置文件
    self.temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix='.json').name
    
    # 创建临时测试数据库文件
    self.db1_path = tempfile.NamedTemporaryFile(
        delete=False, suffix='.sqlite').name
    self.db2_path = tempfile.NamedTemporaryFile(
        delete=False, suffix='.db').name
    
    # 初始化测试数据库
    for db_path in [self.db1_path, self.db2_path]:
      conn = sqlite3.connect(db_path)
      conn.close()

  def tearDown(self):
    """测试后的清理工作，删除临时文件"""
    # 删除临时配置文件
    if os.path.exists(self.temp_file):
      os.remove(self.temp_file)
    
    # 删除临时数据库文件
    for db_path in [self.db1_path, self.db2_path]:
      if os.path.exists(db_path):
        os.remove(db_path)
    
    # 清理可能生成的默认配置文件
    if os.path.exists("diff_config.json"):
      try:
        os.remove("diff_config.json")
      except:
        pass

  def test_default_config(self):
    """测试默认配置"""
    config = DiffConfig.get_default_config()
    self.assertEqual(config.source_database, "db1.sqlite")
    self.assertEqual(config.target_database, "db2.sqlite")

  def test_config_extension_validation(self):
    """测试配置扩展名验证功能"""
    # 测试源数据库不是有效扩展名的情况
    config = DiffConfig(source_database="source.txt", target_database=self.db2_path)
    with self.assertRaises(ValueError):
      config.validate()

    # 测试目标数据库不是有效扩展名的情况
    config = DiffConfig(source_database=self.db1_path, target_database="target.txt")
    with self.assertRaises(ValueError):
      config.validate()
    
    # 测试有效的.db扩展名
    try:
      config = DiffConfig(source_database=self.db2_path, target_database=self.db2_path)
      config.validate()
      self.assertEqual(config.source_database, self.db2_path)
    except ValueError:
      self.fail("DiffConfig应该接受.db扩展名的文件")
    
    # 测试有效的.sqlite扩展名
    try:
      config = DiffConfig(source_database=self.db1_path, target_database=self.db1_path)
      config.validate()
      self.assertEqual(config.source_database, self.db1_path)
    except ValueError:
      self.fail("DiffConfig应该接受.sqlite扩展名的文件")

  def test_file_existence_validation(self):
    """测试文件存在性验证功能"""
    # 测试源数据库文件不存在的情况
    non_existent_file = "non_existent.db"
    try:
      if os.path.exists(non_existent_file):
        os.remove(non_existent_file)
      
      config = DiffConfig(source_database=non_existent_file, target_database=self.db2_path)
      with self.assertRaises(FileNotFoundError):
        config.validate()
    finally:
      if os.path.exists(non_existent_file):
        os.remove(non_existent_file)
    
    # 测试目标数据库文件不存在的情况
    config = DiffConfig(source_database=self.db1_path, target_database=non_existent_file)
    with self.assertRaises(FileNotFoundError):
      config.validate()
    
    # 测试文件存在的情况应该通过验证
    try:
      config = DiffConfig(source_database=self.db1_path, target_database=self.db2_path)
      config.validate()
      self.assertEqual(config.source_database, self.db1_path)
      self.assertEqual(config.target_database, self.db2_path)
    except (ValueError, FileNotFoundError):
      self.fail("DiffConfig应该接受存在的有效数据库文件")

  def test_individual_validation_methods(self):
    """测试单独的验证方法"""
    # 测试source_database单独验证
    config = DiffConfig(source_database=self.db1_path, target_database=self.db2_path)
    self.assertEqual(config.validate_source_database(), self.db1_path)
    
    # 测试target_database单独验证
    self.assertEqual(config.validate_target_database(), self.db2_path)
    
    # 测试source_database验证失败的情况
    config = DiffConfig(source_database="invalid.txt", target_database=self.db2_path)
    with self.assertRaises(ValueError):
      config.validate_source_database()

  def test_save_and_load_config(self):
    """测试保存和加载配置"""
    # 创建自定义配置
    custom_config = DiffConfig(
        source_database=self.db1_path,
        target_database=self.db2_path
    )

    # 保存配置
    custom_config.save_to_file(self.temp_file)

    # 加载配置
    loaded_config = DiffConfig.from_json_file(self.temp_file)

    # 验证加载的配置是否与保存的一致
    self.assertEqual(loaded_config.source_database, self.db1_path)
    self.assertEqual(loaded_config.target_database, self.db2_path)

  def test_auto_create_default_config(self):
    """测试配置文件不存在时自动创建默认配置"""
    # 确保临时文件不存在
    if os.path.exists(self.temp_file):
      os.remove(self.temp_file)
    
    # 创建默认的数据库文件，以通过验证
    default_db_paths = []
    try:
      for db_file in ['db1.sqlite', 'db2.sqlite']:
        if not os.path.exists(db_file):
          conn = sqlite3.connect(db_file)
          conn.close()
          default_db_paths.append(db_file)
      
      # 加载配置（应该自动创建）
      config = DiffConfig.from_json_file(self.temp_file)
      
      # 验证是否创建了文件
      self.assertTrue(os.path.exists(self.temp_file))
      
      # 验证配置是否为默认值
      self.assertEqual(config.source_database, "db1.sqlite")
      self.assertEqual(config.target_database, "db2.sqlite")
    finally:
      # 清理创建的默认数据库文件
      for db_file in default_db_paths:
        if os.path.exists(db_file):
          os.remove(db_file)

  def test_load_invalid_json(self):
    """测试加载无效的JSON配置文件"""
    # 创建包含无效JSON的文件
    with open(self.temp_file, 'w') as f:
      f.write("{invalid json}")
    
    # 测试加载无效JSON时应该抛出ValueError
    with self.assertRaises(ValueError):
      DiffConfig.from_json_file(self.temp_file)

  def test_load_without_validation(self):
    """测试禁用验证加载配置"""
    # 创建配置文件，包含无效的数据库路径
    invalid_config = {
      "source_database": "invalid_source.txt",
      "target_database": "invalid_target.txt"
    }
    
    with open(self.temp_file, 'w') as f:
      json.dump(invalid_config, f, indent=2)
    
    # 禁用验证加载配置
    config = DiffConfig.from_json_file(self.temp_file, validate=False)
    
    # 验证配置值是否正确加载
    self.assertEqual(config.source_database, "invalid_source.txt")
    self.assertEqual(config.target_database, "invalid_target.txt")
    
    # 验证手动调用验证会失败
    with self.assertRaises((ValueError, FileNotFoundError)):
      config.validate()


if __name__ == '__main__':
  unittest.main()