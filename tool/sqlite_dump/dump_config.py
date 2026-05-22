import json
import os
import logging
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('dump.log.txt', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建logger对象
logger = logging.getLogger('sqlite_dump')


class DumpConfig(BaseModel):
  """数据库配置模型，管理源数据库和目标数据库的路径"""
  # 设置extra='allow'以允许在模型中包含未定义的字段
  class Config:
    extra = "allow"
    validate_assignment = False  # 禁用赋值时的自动验证
    arbitrary_types_allowed = True
  
  source_database: str  # 源数据库文件
  target_database: str  # 目标数据库文件

  def validate_source_database(self) -> str:
    """验证源数据库文件是否为sqlite数据库（.db扩展名）"""
    v = self.source_database
    if not v.endswith('.db'):
      raise ValueError('源数据库必须是sqlite数据库文件（.db扩展名）')
    return v

  def validate_target_database(self) -> str:
    """验证目标数据库文件是否为sqlite数据库（.db扩展名）"""
    v = self.target_database
    if not v.endswith('.db'):
      raise ValueError('目标数据库必须是sqlite数据库文件（.db扩展名）')
    return v
  
  def validate(self) -> None:
    """主动调用验证方法，验证所有配置项"""
    # 调用各个字段的验证方法
    self.validate_source_database()
    self.validate_target_database()
    
  @classmethod
  def get_default_config(cls) -> 'DumpConfig':
    """获取默认配置"""
    return cls(
        source_database="source.db",
        target_database="target.db"
    )

  @classmethod
  def from_json_file(cls, file_path: str = "dump_config.json", validate: bool = False) -> 'DumpConfig':
    """从JSON文件加载配置，如果文件不存在则生成默认配置"""
    if not os.path.exists(file_path):
      # 生成默认配置文件
      default_config = cls.get_default_config()
      with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(default_config.dict(), f, indent=2)
      logger.info(f"配置文件 {file_path} 不存在，已生成默认配置")

    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
      
      # 创建配置对象但不进行自动验证
      config = cls(**config_data)
      
      # 如果需要，进行主动验证
      if validate:
        config.validate()
      
      return config
    except json.JSONDecodeError as e:
      error_msg = f"配置文件格式错误: {str(e)}"
      logger.error(error_msg)
      raise ValueError(error_msg)
    except Exception as e:
      # 捕获其他异常并记录日志
      logger.error(f"加载配置时发生错误: {str(e)}")
      raise

  def save_to_file(self, file_path: str = "dump_config.json") -> None:
    """将配置保存到文件"""
    try:
      with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(self.dict(), f, indent=2)
      logger.info(f"配置已成功保存到: {file_path}")
    except Exception as e:
      logger.error(f"保存配置时发生错误: {str(e)}")
      raise