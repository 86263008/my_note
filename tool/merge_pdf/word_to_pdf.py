import sys
import os
from docx2pdf import convert
import argparse

def convert_to_pdf(docx_path, pdf_path):
    try:
        # 使用 python-docx2pdf 进行转换
        convert(docx_path, pdf_path)
    except Exception as e:
        print(f"转换为PDF时出现错误: {str(e)}")

def process_folder(folder_path, output_folder):
    # 获取文件夹名称，并根据名称创建输出文件夹路径
    folder_name = os.path.basename(folder_path)
    output_folder_path = os.path.join(output_folder, folder_name)

    # 创建输出文件夹
    os.makedirs(output_folder_path, exist_ok=True)

    # 遍历文件夹中的文件
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        # 检查文件是否为Word文档
        if file_name.lower().endswith(".docx"):
            # 生成PDF文档的路径，使用与Word文档相同的文件名，不同的扩展名
            pdf_file_name = os.path.splitext(file_name)[0] + ".pdf"
            pdf_path = os.path.join(output_folder_path, pdf_file_name)

            # 转换Word文档为PDF
            convert_to_pdf(file_path, pdf_path)

        # 如果文件是文件夹，则递归处理子文件夹
        elif os.path.isdir(file_path):
            process_folder(file_path, output_folder_path)

if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="Convert Word documents to PDF.")
    parser.add_argument("input_folder", help="Path to the input folder.")
    parser.add_argument("output_folder", help="Path to the output folder.")

    # 解析命令行参数
    args = parser.parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder

    # 调用递归函数处理文件夹
    process_folder(input_folder, output_folder)