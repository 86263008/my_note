# PDF转Word（pdf2docx）操作说明（含venv虚拟环境搭建）

## 一、整体说明
本文档适用于Windows/macOS/Linux系统，核心目标是：
1. 搭建独立的Python虚拟环境（避免依赖冲突）；
2. 使用pdf2docx库实现PDF转Word（.docx），支持基础转换、指定页码、忽略图片等进阶操作。

## 二、前置条件
1. 已安装Python 3.7及以上版本（推荐3.8-3.10，兼容性最佳）；
   - 验证方法：打开终端/CMD，输入 `python --version`（Windows）或 `python3 --version`（macOS/Linux），能显示版本号即安装成功；
   - 若未安装：从[Python官网](https://www.python.org/downloads/)下载对应系统版本，安装时勾选「Add Python to PATH」（Windows）。
2. 待转换的PDF文件为「可编辑文本型」（扫描件/图片型PDF需额外OCR处理，本文档末尾补充说明）。

## 三、步骤1：搭建venv虚拟环境

### 3.1 创建虚拟环境
在工作目录下执行以下命令，创建名为`.venv`的虚拟环境：
```bash
py -m venv .venv
```
执行后，工作目录会生成`.venv`文件夹，包含独立的Python解释器和依赖库。

### 3.3 激活虚拟环境

```bash
.venv\Scripts\activate.bat
```

## 四、步骤2：安装pdf2docx库
激活虚拟环境后，执行以下命令安装pdf2docx（虚拟环境内安装的库仅在此环境生效）：
```bash
pip install pdf2docx
```
- 若安装慢：可使用国内镜像源加速：
  ```bash
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pdf2docx
  ```
- 验证安装：输入`pip list`，能看到`pdf2docx`及依赖包（如`PyMuPDF`）即安装成功。

## 五、步骤3：PDF转Word实操
### 5.1 基础用法（单文件完整转换）
#### 5.1.1 准备文件
将待转换的PDF文件（如`test.pdf`）复制到`pdf2docx_work`目录下。

#### 5.1.2 编写转换脚本
在工作目录下新建`pdf2docx_convert.py`文件（可用记事本/VS Code/文本编辑器），内容如下：

```python
# pdf2docx_convert.py
from pdf2docx import Converter
import os

# 1. 定义文件路径（修改为你的PDF文件名和输出Word名）
pdf_file = "test.pdf"  # 待转换的PDF文件名
docx_file = "test_converted.docx"  # 输出的Word文件名

# 2. 检查PDF文件是否存在
if not os.path.exists(pdf_file):
    print(f"错误：未找到PDF文件 {pdf_file}，请检查文件路径！")
else:
    # 3. 初始化转换器并执行转换
    try:
        cv = Converter(pdf_file)
        cv.convert(docx_file)  # 核心转换方法
        cv.close()  # 释放资源
        print(f"转换成功！Word文件已保存至：{os.path.abspath(docx_file)}")
    except Exception as e:
        print(f"转换失败：{str(e)}")
```

#### 5.1.3 运行脚本
在激活的虚拟环境中执行：
```bash
python pdf_word.py
```

## 六、步骤4：退出虚拟环境（可选）
转换完成后，执行以下命令退出虚拟环境（不影响已生成的Word文件）：
```bash
deactivate
```
退出后，终端提示符前的`(.venv)`会消失。
