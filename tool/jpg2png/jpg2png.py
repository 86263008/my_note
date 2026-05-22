import cv2
import numpy as np
from PIL import Image
import os

def process_seal_image(
    input_path, 
    output_path=None, 
    target_physical_size=(38, 38),  # 物理尺寸(mm)，默认38mm×38mm
    dpi=300,                        # 分辨率，300dpi适合印刷
    threshold=240
):
    """
    处理公章图片：透明化背景 + 边缘裁剪 + 尺寸适配 + 分辨率设置
    
    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径
        target_physical_size: 目标物理尺寸(mm)，(宽, 高)
        dpi: 分辨率(像素/英寸)，影响物理尺寸精度
        threshold: 背景分割阈值
    """
    input_path = str(input_path)
    
    if output_path is None:
        filename, _ = os.path.splitext(input_path)
        output_path = f"{filename}_processed.png"
    output_path = str(output_path)
    
    try:
        # 1. 读取图片并处理
        with Image.open(input_path) as pil_img:
            # 处理不同模式的图片
            if pil_img.mode in ('RGBA', 'LA'):
                # 处理透明背景图片，转为白色背景
                background = Image.new(pil_img.mode[:-1], pil_img.size, (255, 255, 255))
                background.paste(pil_img, pil_img.split()[-1])
                img_rgb = np.array(background)
            else:
                # 转为RGB模式
                img_rgb = np.array(pil_img.convert('RGB'))
        
        # 2. 背景透明化
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 3. 边缘检测与裁剪
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise ValueError("未检测到有效轮廓，无法裁剪")
        
        # 找到最大轮廓
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        
        # 裁剪图像
        cropped_rgb = img_rgb[y:y+h, x:x+w]
        cropped_mask = mask[y:y+h, x:x+w]
        
        # 4. 计算目标像素尺寸（根据物理尺寸和DPI）
        # 1英寸 = 25.4毫米
        target_pixel_width = int(target_physical_size[0] * dpi / 25.4)
        target_pixel_height = int(target_physical_size[1] * dpi / 25.4)
        target_size = (target_pixel_width, target_pixel_height)
        
        # 5. 保持比例缩放
        scale = min(target_size[0] / w, target_size[1] / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 缩放图像
        resized_rgb = cv2.resize(cropped_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(cropped_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 6. 放置在目标尺寸中心
        result = np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)
        x_offset = (target_size[0] - new_w) // 2
        y_offset = (target_size[1] - new_h) // 2
        
        # 填充RGB和Alpha通道
        result[y_offset:y_offset+new_h, x_offset:x_offset+new_w, :3] = resized_rgb
        result[y_offset:y_offset+new_h, x_offset:x_offset+new_w, 3] = resized_mask
        
        # 7. 保存图片并设置DPI（关键：确保物理尺寸准确）
        pil_result = Image.fromarray(result, mode='RGBA')
        pil_result.save(output_path, dpi=(dpi, dpi))  # 设置分辨率
        
        print(f"处理成功: {input_path} -> {output_path}")
        print(f"物理尺寸: {target_physical_size[0]}mm × {target_physical_size[1]}mm (@{dpi}dpi)")
        return True
    
    except Exception as e:
        print(f"处理失败 {input_path}: {str(e)}")
        return False

def batch_process_seals():
    """批量处理当前目录下所有图片"""
    current_dir = os.getcwd()
    all_files = os.listdir(current_dir)
    
    # 筛选图片文件
    image_files = [
        f for f in all_files 
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        and os.path.isfile(os.path.join(current_dir, f))
    ]
    
    if not image_files:
        print("未找到任何图片文件")
        return
    
    print(f"找到 {len(image_files)} 个图片文件，开始批量处理...")
    
    # 其他企业所属部门及个体、私营企业的印章尺寸：38mm×38mm
    for img_file in image_files:
        process_seal_image(
            img_file,
            target_physical_size=(38, 38),  # 物理尺寸(mm)
            dpi=300,                        # 分辨率，300dpi适合印刷和Word显示
            threshold=230
        )
    
    print("批量处理完成！")

if __name__ == "__main__":
    batch_process_seals()
    
    # 如需处理其他尺寸，可直接调用process_seal_image，例如：
    # process_seal_image(
    #     "input.jpg", 
    #     target_physical_size=(42, 42),  # 42mm×42mm
    #     dpi=300
    # )
