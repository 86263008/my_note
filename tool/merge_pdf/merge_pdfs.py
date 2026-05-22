import os
from PyPDF2 import PdfWriter, PdfReader
import argparse

def merge_pdfs_from_folder(folder_path: str, output_file: str):
    """
    合并指定文件夹中的所有PDF文件到一个单一的PDF文件中
    
    参数:
        folder_path (str): 包含要合并的PDF文件的文件夹路径
        output_file (str): 合并后的PDF文件的输出路径
    
    返回值:
        None: 函数执行完成后会将合并结果保存到指定的输出文件中
    
    功能说明:
        1. 扫描指定文件夹，找出所有扩展名以.pdf结尾的文件
        2. 按文件夹中的默认顺序依次读取每个PDF文件
        3. 将每个PDF文件的所有页面添加到合并PDF中
        4. 将合并后的所有页面写入到指定的输出文件
        5. 打印完成信息，显示输出文件路径
    """
    # 获取文件夹中所有的PDF文件（不区分大小写）
    pdf_files = [file for file in os.listdir(folder_path) if file.lower().endswith(".pdf")]

    # 创建一个PDF写入器对象，用于存储合并后的所有页面
    pdf_writer = PdfWriter()

    # 遍历每个PDF文件并将其所有页面添加到写入器中
    for pdf_file in pdf_files:
        # 构建完整的文件路径
        file_path = os.path.join(folder_path, pdf_file)
        # 以二进制只读模式打开PDF文件
        with open(file_path, "rb") as file:
            # 创建PDF读取器对象
            pdf_reader = PdfReader(file)
            # 遍历当前PDF的每一页并添加到写入器
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

    # 将合并后的所有页面写入到输出文件
    with open(output_file, "wb") as output:
        pdf_writer.write(output)

    # 打印合并完成信息，方便用户确认
    print(f"合并完成，保存为：{output_file}")

if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="合并指定文件夹中的PDF文件.")
    parser.add_argument("folder_path", help="要合并的文件夹路径.")
    parser.add_argument("output_file", help="输出的合并后的PDF文件路径.")

    # 解析命令行参数
    args = parser.parse_args()
    folder_path = args.folder_path
    output_file = args.output_file

    merge_pdfs_from_folder(folder_path, output_file)