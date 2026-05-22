"""
分组名单学号检查工具
功能：检查分组名单中每个学号是否出现在学生名单中，如果未出现则输出到CSV文件

作者：自动生成
日期：2026年
"""

import pandas as pd
import os
import json
import argparse
import logging
from typing import List, Dict

# 配置日志
logging.basicConfig(
    filename='check_group_students.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    encoding='utf-8'
)

def load_student_list(student_file_path: str) -> set:
    """
    加载学生名单文件，返回学号集合
    
    参数:
    student_file_path: str - 学生名单Excel文件路径
    
    返回:
    set - 学生学号集合
    """
    print(f"📋 正在加载学生名单: {os.path.basename(student_file_path)}")
    logging.info(f"开始加载学生名单文件: {os.path.basename(student_file_path)}")
    
    try:
        student_df = pd.read_excel(student_file_path)
        
        # 验证学生名单格式
        required_columns = ['学号']
        missing_columns = [col for col in required_columns if col not in student_df.columns]
        if missing_columns:
            error_msg = f"学生名单缺少必要列: {', '.join(missing_columns)}，当前列：{list(student_df.columns)}"
            print(f"❌ {error_msg}")
            logging.error(f"加载学生名单文件 {os.path.basename(student_file_path)} 失败: {error_msg}")
            raise ValueError(error_msg)
        
        # 数据清洗
        # 1. 处理学号为字符串格式
        student_df['学号'] = student_df['学号'].astype(str).str.strip().str.replace(' ', '')
        
        # 2. 去除重复学号和空值
        student_df = student_df.dropna(subset=['学号'])
        student_df = student_df.drop_duplicates(subset=['学号'], keep='first')
        
        # 构建学号集合
        student_ids = set(student_df['学号'])
        
        print(f"   - 总学生人数: {len(student_ids)} 人")
        logging.info(f"成功加载学生名单文件: {os.path.basename(student_file_path)}, 总学生人数: {len(student_ids)}")
        
        return student_ids
    
    except Exception as e:
        print(f"❌ 读取学生名单失败: {str(e)}")
        logging.error(f"加载学生名单文件 {os.path.basename(student_file_path)} 失败: {str(e)}")
        raise

def load_group_list(group_file_path: str) -> List[Dict]:
    """
    加载分组名单文件，返回分组信息列表
    
    参数:
    group_file_path: str - 分组名单Excel文件路径
    
    返回:
    List[Dict] - 分组信息列表，每个字典包含组号、题目、所有学号信息
    """
    print(f"📋 正在加载分组名单: {os.path.basename(group_file_path)}")
    logging.info(f"开始加载分组名单文件: {os.path.basename(group_file_path)}")
    
    try:
        df = pd.read_excel(group_file_path)
        
        # 验证文件格式：检查是否有足够的列
        if len(df.columns) < 6:
            error_msg = f"分组名单至少需要6列数据（题目、项目经理学号、4个成员学号），当前只有{len(df.columns)}列"
            print(f"❌ {error_msg}")
            logging.error(f"加载分组名单文件 {os.path.basename(group_file_path)} 失败: {error_msg}")
            raise ValueError(error_msg)
        
        # 按列顺序重命名为固定列名，不依赖原始表头
        fixed_columns = ['题目', '项目经理学号', '成员1学号', '成员2学号', '成员3学号', '成员4学号']
        # 只重命名前6列，忽略可能存在的额外列
        df = df.iloc[:, :6].rename(columns=dict(zip(df.columns[:6], fixed_columns)))
        
        # 数据清洗：将所有学号转换为字符串格式，处理浮点数情况
        for col in ['项目经理学号', '成员1学号', '成员2学号', '成员3学号', '成员4学号']:
            # 自定义函数：将值转换为字符串，处理浮点数
            def convert_to_str(x):
                if pd.isna(x):
                    return ''
                # 如果是浮点数且可以转换为整数，去掉小数部分
                if isinstance(x, float) and x.is_integer():
                    return str(int(x))
                return str(x).strip().replace(' ', '')
            
            df[col] = df[col].apply(convert_to_str)
        
        # 构建分组信息列表
        groups = []
        for idx, row in df.iterrows():
            group_info = {
                '组号': idx + 1,
                '题目': row['题目'],
                '学号信息': [
                    {'类型': '项目经理', '学号': row['项目经理学号']},
                    {'类型': '成员1', '学号': row['成员1学号']},
                    {'类型': '成员2', '学号': row['成员2学号']},
                    {'类型': '成员3', '学号': row['成员3学号']},
                    {'类型': '成员4', '学号': row['成员4学号']}
                ]
            }
            groups.append(group_info)
        
        print(f"   - 总组数: {len(groups)} 组")
        logging.info(f"成功加载分组名单文件: {os.path.basename(group_file_path)}, 总组数: {len(groups)}")
        
        return groups
    
    except Exception as e:
        print(f"❌ 读取分组名单失败: {str(e)}")
        logging.error(f"加载分组名单文件 {os.path.basename(group_file_path)} 失败: {str(e)}")
        raise

def check_group_students(student_ids: set, groups: List[Dict]) -> List[Dict]:
    """
    检查分组名单中的学号是否在学生名单中存在
    
    参数:
    student_ids: set - 学生学号集合
    groups: List[Dict] - 分组信息列表
    
    返回:
    List[Dict] - 不存在的学号信息列表
    """
    print("🔍 开始检查分组名单中的学号")
    logging.info("开始检查分组名单中的学号")
    
    missing_students = []
    total_checked = 0
    missing_count = 0
    
    for group in groups:
        group_num = group['组号']
        topic = group['题目']
        
        for student_info in group['学号信息']:
            student_type = student_info['类型']
            student_id = student_info['学号']
            
            # 跳过空学号
            if not student_id:
                continue
            
            total_checked += 1
            
            if student_id not in student_ids:
                missing_count += 1
                missing_students.append({
                    '组号': group_num,
                    '题目': topic,
                    '类型': student_type,
                    '学号': student_id
                })
                print(f"   - 组{group_num} {topic} - {student_type}: {student_id} 未在学生名单中找到")
                logging.warning(f"组{group_num} {topic} - {student_type}: {student_id} 未在学生名单中找到")
    
    print(f"✅ 检查完成，共检查 {total_checked} 个学号，其中 {missing_count} 个未在学生名单中找到")
    logging.info(f"检查完成，共检查 {total_checked} 个学号，其中 {missing_count} 个未在学生名单中找到")
    
    return missing_students

def save_missing_students(missing_students: List[Dict], output_file: str) -> None:
    """
    将不存在的学号输出到CSV文件
    
    参数:
    missing_students: List[Dict] - 不存在的学号信息列表
    output_file: str - 输出CSV文件路径
    """
    if not missing_students:
        print(f"✅ 没有未找到的学号，跳过保存")
        logging.info("没有未找到的学号，跳过保存")
        return
    
    print(f"💾 正在保存未找到的学号到: {output_file}")
    logging.info(f"开始保存未找到的学号到: {output_file}")
    
    try:
        # 创建DataFrame
        df = pd.DataFrame(missing_students)
        
        # 保存到CSV文件
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 保存成功！共保存 {len(df)} 条记录")
        logging.info(f"成功保存未找到的学号到: {output_file}，共 {len(df)} 条记录")
    
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")
        logging.error(f"保存文件失败: {str(e)}")
        raise

def main():
    """
    主程序入口
    """
    print("=" * 70)
    print("          分组名单学号检查工具          ")
    print("=" * 70)
    logging.info("分组名单学号检查工具开始运行")
    
    # ------------------- 命令行参数解析 -------------------
    parser = argparse.ArgumentParser(description='分组名单学号检查工具')
    parser.add_argument('--data-dir', type=str, default='', help='数据目录路径，默认为当前目录')
    parser.add_argument('--output-file', type=str, default='', help='输出CSV文件路径，默认为数据目录下的missing_students.csv')
    args = parser.parse_args()
    
    # 确定数据目录
    data_dir = args.data_dir if args.data_dir else os.getcwd()
    
    print(f"📁 数据目录: {data_dir}")
    logging.info(f"使用数据目录: {data_dir}")
    
    # ------------------- 配置区域 -------------------
    # 从config.json文件读取配置
    try:
        config_path = os.path.join(data_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 从配置中读取文件路径，并与数据目录结合
        # 如果配置中没有指定，使用默认文件名
        default_student_file = '名单.xlsx'
        default_group_file = '分组名单.xlsx'
        
        STUDENT_FILE_PATH = os.path.join(data_dir, config.get('STUDENT_FILE_PATH', default_student_file))
        
        # 处理分组名单文件路径，为空时使用默认文件名
        GROUP_LIST_PATH = None
        group_file_config = config.get('GROUP_LIST_PATH')
        if group_file_config:
            GROUP_LIST_PATH = os.path.join(data_dir, group_file_config)
        else:
            GROUP_LIST_PATH = os.path.join(data_dir, default_group_file)
        
        # 确定输出文件路径
        OUTPUT_FILE_PATH = args.output_file if args.output_file else os.path.join(data_dir, 'missing_students.csv')
        
        print(f"📁 配置文件加载成功: config.json")
        print(f"   - 学生名单文件: {os.path.basename(STUDENT_FILE_PATH)}")
        print(f"   - 分组名单文件: {os.path.basename(GROUP_LIST_PATH)}")
        print(f"   - 输出文件: {os.path.basename(OUTPUT_FILE_PATH)}")
        
        logging.info(f"配置文件加载成功，学生名单文件: {os.path.basename(STUDENT_FILE_PATH)}, 输出文件: {os.path.basename(OUTPUT_FILE_PATH)}, 分组名单文件: {os.path.basename(GROUP_LIST_PATH)}")
        
    except FileNotFoundError:
        print(f"❌ 配置文件 config.json 未找到")
        logging.error(f"配置文件 config.json 未找到")
        exit(1)
    except json.JSONDecodeError:
        print(f"❌ 配置文件格式错误，不是有效的JSON格式")
        logging.error(f"配置文件格式错误，不是有效的JSON格式")
        exit(1)
    
    # ------------------- 执行流程 -------------------
    try:
        # 1. 加载学生名单
        student_ids = load_student_list(STUDENT_FILE_PATH)
        
        # 2. 加载分组名单
        groups = load_group_list(GROUP_LIST_PATH)
        
        # 3. 检查学号是否存在
        missing_students = check_group_students(student_ids, groups)
        
        # 4. 保存未找到的学号到CSV文件
        save_missing_students(missing_students, OUTPUT_FILE_PATH)
        
        print(f"\n" + "=" * 70)
        print("          程序执行完成！          ")
        if missing_students:
            print(f"📁 输出文件: {os.path.abspath(OUTPUT_FILE_PATH)}")
        print("=" * 70)
        logging.info(f"程序执行完成，输出文件: {os.path.abspath(OUTPUT_FILE_PATH)}")
          
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        print("请检查：1.文件路径是否正确 2.文件格式是否符合要求 3.是否有读取权限")
        logging.error(f"程序执行出错: {str(e)}")
        exit(1)

# 程序入口
if __name__ == "__main__":
    main()
