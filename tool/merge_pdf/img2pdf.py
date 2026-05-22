from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
import os
import argparse

def resize_by_orientation(image, max_width):
    """
    延最长边等比例缩放图像
    
    :param image: PIL.Image对象（已打开的图像）
    :param max_width: 最大尺寸（宽或高）
    :return: 缩放后的Image对象
    """
    # 获取原图尺寸
    original_w, original_h = image.size
    
    # 延最长边计算缩放比例
    if original_w >= original_h:
        scale_ratio = max_width / original_w
    else:
        scale_ratio = max_width / original_h
    
    # 计算目标尺寸（转为整数）
    target_w = int(original_w * scale_ratio)
    target_h = int(original_h * scale_ratio)
    target_size = (target_w, target_h)
    
    # 执行缩放（使用高质量插值算法）
    resized_image = image.resize(target_size, resample=Image.Resampling.LANCZOS)
    
    return resized_image


def convert_image_to_pdf(image_path, output_path):
    image = Image.open(image_path)

    a4_long = int(11.69 * 300)
    a4_short = int(8.27 * 300)
    # 根据图像的宽度和高度判断页面方向
    if image.width > image.height:
        # 横向页面，计算A4纸张的像素尺寸
        a4_width = a4_long  # 11.69英寸乘以300 DPI
        a4_height = a4_short  # 8.27英寸乘以300 DPI
    else:
        # 纵向页面，计算A4纸张的像素尺寸
        a4_width = a4_short  # 8.27英寸乘以300 DPI
        a4_height = a4_long  # 11.69英寸乘以300 DPI

    # 缩放图像以适应A4页面并保持纵横比
    image_scaled = resize_by_orientation(image, a4_long)

    # 创建一个新的A4大小的空白图像
    a4_image = Image.new("RGB", (a4_width, a4_height), (255, 255, 255))

    # 获取图像的实际大小和空白边距
    image_width, image_height = image.size
    left = 0# (a4_width - image_width) // 2
    top = 0#(a4_height - image_height) // 2

    # 粘贴缩放后的图像到A4图像中心，并去除页面留白
    a4_image.paste(image_scaled, (left, top))

    # 将A4图像保存为PDF
    pdf_path = output_path + ".pdf"
    a4_image.save(pdf_path, "PDF", resolution=300)
    return pdf_path


def merge_pdfs(pdfs, output_path):
    writer = PdfWriter()

    for pdf in pdfs:
        with open(pdf, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                writer.add_page(page)

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    # 删除各个PDF文件
    for pdf in pdfs:
        os.remove(pdf)

def process_folder(folder_path, output_folder):
    folder_name = os.path.basename(folder_path)
    output_pdf = os.path.join(output_folder, f"{folder_name}.pdf")

    # 查找图像文件夹中所有的图片文件
    image_files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path)
                   if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))]

    # 转换图像为PDF并获取PDF路径列表
    pdfs = []
    for image_file in image_files:
        output_path = os.path.join(output_folder, os.path.splitext(os.path.basename(image_file))[0])
        pdf_path = convert_image_to_pdf(image_file, output_path)
        pdfs.append(pdf_path)

    # 合并所有PDF文件
    merge_pdfs(pdfs, output_pdf)

    # 递归处理子文件夹
    subfolders = [os.path.join(folder_path, subfolder) for subfolder in os.listdir(folder_path)
                  if os.path.isdir(os.path.join(folder_path, subfolder))]
    for subfolder in subfolders:
        process_folder(subfolder, output_folder)

if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="Convert and merge images to PDF.")
    parser.add_argument("image_folder", help="Path to the image folder.")
    parser.add_argument("output_folder", help="Path to the output folder.")

    # 解析命令行参数
    args = parser.parse_args()
    image_folder = args.image_folder
    output_folder = args.output_folder

    # 调用递归函数处理图像目录
    process_folder(image_folder, output_folder)
