import os
import json
import tempfile
import unittest
from dump_config import DumpConfig


class TestDumpConfig(unittest.TestCase):
  """测试DumpConfig类的功能"""

  def setUp(self):
    """测试前的准备工作，创建临时文件"""
    # 创建临时配置文件
    self.temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix='.json').name

  def tearDown(self):
    """测试后的清理工作，删除临时文件"""
    if os.path.exists(self.temp_file):
      os.remove(self.temp_file)

    # 清理可能生成的默认数据库文件
    for db_file in ['source.db', 'target.db']:
      if os.path.exists(db_file):
        os.remove(db_file)

  def test_default_config(self):
    """测试默认配置"""
    config = DumpConfig.get_default_config()
    self.assertEqual(config.source_database, "source.db")
    self.assertEqual(config.target_database, "target.db")
    
    # 验证默认配置应该通过校验
    try:
      config.validate()
    except ValueError:
      self.fail("默认配置应该通过校验")

  def test_config_validation(self):
    """测试配置验证功能"""
    # 测试源数据库不是.db文件的情况
    config = DumpConfig(source_database="source.txt", target_database="target.db")
    with self.assertRaises(ValueError):
      config.validate()

    # 测试目标数据库不是.db文件的情况
    config = DumpConfig(source_database="source.db", target_database="target.txt")
    with self.assertRaises(ValueError):
      config.validate()
    
    # 测试有效的配置应该通过校验
    try:
      config = DumpConfig(source_database="valid_source.db", target_database="valid_target.db")
      config.validate()
      self.assertEqual(config.source_database, "valid_source.db")
      self.assertEqual(config.target_database, "valid_target.db")
    except ValueError:
      self.fail("有效的.db文件路径应该通过校验")

  def test_individual_validation_methods(self):
    """测试单独的验证方法"""
    # 测试source_database单独验证
    config = DumpConfig(source_database="test.db", target_database="test.db")
    self.assertEqual(config.validate_source_database(), "test.db")
    
    # 测试target_database单独验证
    self.assertEqual(config.validate_target_database(), "test.db")
    
    # 测试source_database验证失败的情况
    config = DumpConfig(source_database="invalid.txt", target_database="test.db")
    with self.assertRaises(ValueError):
      config.validate_source_database()
    
    # 测试target_database验证失败的情况
    config = DumpConfig(source_database="test.db", target_database="invalid.txt")
    with self.assertRaises(ValueError):
      config.validate_target_database()

  def test_save_and_load_config(self):
    """测试保存和加载配置"""
    # 创建自定义配置
    custom_config = DumpConfig(
        source_database="test_source.db",
        target_database="test_target.db"
    )
    
    # 验证配置
    custom_config.validate()

    # 保存配置
    custom_config.save_to_file(self.temp_file)

    # 加载配置
    loaded_config = DumpConfig.from_json_file(self.temp_file)

    # 验证加载的配置是否与保存的一致
    self.assertEqual(loaded_config.source_database, "test_source.db")
    self.assertEqual(loaded_config.target_database, "test_target.db")
    
    # 验证加载的配置通过验证
    loaded_config.validate()

  def test_auto_create_default_config(self):
    """测试配置文件不存在时自动创建默认配置"""
    # 确保临时文件不存在
    if os.path.exists(self.temp_file):
      os.remove(self.temp_file)

    # 加载配置（应该自动创建）
    config = DumpConfig.from_json_file(self.temp_file)

    # 验证是否创建了文件
    self.assertTrue(os.path.exists(self.temp_file))

    # 验证配置是否为默认值
    self.assertEqual(config.source_database, "source.db")
    self.assertEqual(config.target_database, "target.db")
    
    # 验证自动创建的配置通过验证
    config.validate()

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
    config = DumpConfig.from_json_file(self.temp_file, validate=False)
    
    # 验证配置值是否正确加载
    self.assertEqual(config.source_database, "invalid_source.txt")
    self.assertEqual(config.target_database, "invalid_target.txt")
    
    # 验证手动调用验证会失败
    with self.assertRaises(ValueError):
      config.validate()


if __name__ == '__main__':
  unittest.main()