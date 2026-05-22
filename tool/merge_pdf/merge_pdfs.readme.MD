# 操作步骤

1. 使用*venv*创建虚拟环境目录`.venv`

```bash
py -m venv .venv
```

2. 激活/反激活虚拟环境：

```bash
.venv\scripts\activate
```
```bash
.venv\scripts\deactivate
```

3. 安装依赖（首次）

```bash
pip install PyPDF2
```

4. Pdf转Word

**执行命令格式**

```bash
python merge_pdfs.py <folder_path> <output_file>
```

**命令行参数说明**

1. **folder_path**（必需参数）

    - 类型：字符串
    - 描述：包含要合并的PDF文件的文件夹路径
    - 可以是相对路径或绝对路径

2. **output_file**（必需参数）
    - 类型：字符串
    - 描述：合并后的PDF文件的输出路径和文件名
    - 可以是相对路径或绝对路径
    - 文件名应当包含`.pdf`扩展名

**示例1：使用相对路径**

将当前目录下pdf文件夹中的所有PDF文件合并为merged.pdf

```bash
py merge_pdfs.py liu pdf_out/liu.pdf
```