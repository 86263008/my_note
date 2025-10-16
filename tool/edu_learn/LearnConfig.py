import json
import os

class LearnConfig:
    def __init__(self, file_path="config.json"):
        """初始化配置读取器，若配置文件不存在则使用默认参数并创建配置文件
        
        Args:
            file_path (str): JSON配置文件的路径，默认为"config.json"
        """
        self.file_path = file_path  # 配置文件的路径
        # 设置默认参数
        self.default_email = "86263008@qq.com"
        self.default_chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.default_nav_title = "2025年暑假教师研修"
        self.default_duration_per_class = 50

        # 初始化属性
        self.email = self.default_email  # 学习者邮箱地址
        self.chrome_path = self.default_chrome_path  # 存储Chrome浏览器安装路径
        self.nav_title = self.default_nav_title  # 课程导航页面标题
        self.duration_per_class = self.default_duration_per_class  # 每个课程学习时间（分钟）
        
        # 尝试加载配置文件
        self.load_config()
    
    def load_config(self):
        """加载并解析JSON配置文件，若文件不存在则创建并写入默认配置"""
        try:
            # 检查文件是否存在
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                    # 更新配置项
                    if "email" in data:
                        self.email = data["email"]
                    if "chrome_path" in data:
                        self.chrome_path = data["chrome_path"]
                    if "nav_title" in data:
                        self.nav_title = data["nav_title"]
                    if "duration_per_class" in data:
                        self.duration_per_class = data["duration_per_class"] if data["duration_per_class"] > 0 else self.default_duration_per_class

                return True
            else:
                # 文件不存在，创建并写入默认配置
                self._create_default_config()
                print(f"配置文件 '{self.file_path}' 不存在，已创建并使用默认配置")
                return False
                
        except json.JSONDecodeError:
            print(f"警告: 配置文件 '{self.file_path}' 格式无效，将使用默认配置并覆盖文件")
            self._create_default_config()
        except Exception as e:
            print(f"加载配置时发生错误: {str(e)}，将使用默认配置并覆盖文件")
            self._create_default_config()
        
        return False
    
    def _create_default_config(self):
        """创建默认配置文件并写入默认参数"""
        try:
            # 准备默认配置数据
            default_config = {
                "email": self.default_email,
                "chrome_path": self.default_chrome_path,
                "nav_title": self.default_nav_title
            }
            
            # 写入文件
            with open(self.file_path, 'w', encoding='utf-8') as file:
                # 使用indent参数使JSON文件格式化，便于阅读
                json.dump(default_config, file, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"创建默认配置文件失败: {str(e)}")
    
    def __str__(self):
        """返回配置信息的字符串表示"""
        return f"LearnConfig(email: {self.email}, chrome_path: {self.chrome_path})"


# 使用示例
if __name__ == "__main__":
    # 创建配置读取器实例
    config = LearnConfig()
    
    # 直接访问数据成员
    print(f"邮箱: {config.email}")
    print(f"Chrome路径: {config.chrome_path}")
    
    # 打印配置信息
    print(config)
    