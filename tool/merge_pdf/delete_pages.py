from PyPDF2 import PdfWriter, PdfReader
import argparse

def delete_pages(pdf_file, pages_to_delete, output_file):
    # 创建一个 PDF 读取器
    pdf_reader = PdfReader(pdf_file)

    # 创建一个 PDF 写入器
    pdf_writer = PdfWriter()

    # 遍历每一页，判断是否需要删除
    for page_number, page in enumerate(pdf_reader.pages):        
        if page_number + 1 not in pages_to_delete:
            pdf_writer.add_page(page)

    # 将写入器中的页面保存到输出文件中
    with open(output_file, 'wb') as output:
        pdf_writer.write(output)

    print(f"删除完成，保存为：{output_file}")

if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="从PDF文件中删除指定页面.")
    parser.add_argument("pdf_file", help="要删除页面的PDF文件路径.")
    parser.add_argument("pages_to_delete", nargs="+", type=int, help="要删除的页面页码，以空格分隔.")
    parser.add_argument("output_file", help="输出的PDF文件路径.")

    # 解析命令行参数
    args = parser.parse_args()
    pdf_file = args.pdf_file
    pages_to_delete = args.pages_to_delete
    output_file = args.output_file

    delete_pages(pdf_file, pages_to_delete, output_file)
