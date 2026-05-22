import argparse
from pdf2docx import Converter

def convert_pdf_to_word(pdf_file, output_file):
    cv = Converter(pdf_file)
    cv.convert(output_file, start=0, end=None)
    cv.close()

    print(f"转换完成，保存为：{output_file}")

if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="将PDF文件转换为Word文档.")
    parser.add_argument("pdf_file", help="要转换的PDF文件路径.")
    parser.add_argument("output_file", help="输出的Word文档路径.")

    # 解析命令行参数
    args = parser.parse_args()
    pdf_file = args.pdf_file
    output_file = args.output_file

    convert_pdf_to_word(pdf_file, output_file)
