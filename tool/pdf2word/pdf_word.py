# pdf2docx_convert.py
from pdf2docx import Converter
import os

# 1. 定义文件路径（修改为你的PDF文件名和输出Word名）
pdf_file = "d2l-zh-pytorch.pdf"  # 待转换的PDF文件名
docx_file = "d2l-zh-pytorch.docx"  # 输出的Word文件名

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