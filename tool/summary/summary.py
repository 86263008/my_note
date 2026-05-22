"""
学生作业成绩汇总系统
功能：根据学生名单和多个作业文件，自动提取并汇总学生的作业成绩
特点：支持灵活扩展，可轻松添加新的作业文件

作者：自动生成
日期：2026年
"""

import pandas as pd
import numpy as np
import os
import json
import logging
import argparse
from typing import List, Tuple, Optional, Dict

# 配置日志
logging.basicConfig(
    filename='成绩汇总.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    encoding='utf-8'
)

def process_homework_file(file_path: str, homework_name: str) -> Optional[pd.DataFrame]:
    """
    处理单个作业文件，提取学号和对应作业分数
    
    参数:
    file_path: str - 作业Excel文件的完整路径
    homework_name: str - 作业名称标识（如"作业1"、"作业2"、"实验报告1"等）
    
    返回:
    pd.DataFrame - 包含两列：学号、[作业名称]分数；若处理失败返回None
    """
    print(f"🔍 正在解析作业文件: {os.path.basename(file_path)}")
    logging.info(f"开始处理作业文件: {os.path.basename(file_path)}")
    
    try:
    # 读取作业文件，跳过前两行（标题行和空行）
        df = pd.read_excel(file_path, skiprows=2)
        
        # 提取学号列（第一列）和分数列（第九列，索引为8）
        # 注：此列索引基于当前作业文件格式，若格式变化需调整
        if df.shape[1] < 9:
            error_msg = f"作业文件格式错误，列数不足9列，实际列数：{df.shape[1]}"
            print(f"❌ {error_msg}")
            logging.error(f"处理作业文件 {os.path.basename(file_path)} 失败: {error_msg}")
            return None
        
        result_df = df.iloc[:, [0, 8]].copy()
        result_df.columns = ['学号', f'{homework_name}分数']
        
        # ------------------- 数据清洗流程 -------------------
        # 1. 去除学号为空的行
        initial_count = len(result_df)
        result_df = result_df.dropna(subset=['学号'])
        print(f"   - 移除空学号记录: {initial_count - len(result_df)} 条")
        
        # 2. 处理学号数据类型，确保为字符串格式（避免数字型学号丢失前导零）
        result_df['学号'] = result_df['学号'].astype(str)
        # 清理学号中的特殊字符和空格
        result_df['学号'] = result_df['学号'].str.strip().str.replace(' ', '')
        
        # 3. 处理分数数据
        def clean_score(score) -> float:
            """清理分数数据，非数值型或空值返回0（表示未交）"""
            if pd.isna(score):
                return 0.0
            try:
                # 处理可能包含的百分号或其他字符
                score_str = str(score).strip().replace('%', '')
                return float(score_str)
            except (ValueError, TypeError):
                return 0.0
        
        result_df[f'{homework_name}分数'] = result_df[f'{homework_name}分数'].apply(clean_score)
        
        # 4. 去除重复的学号记录，保留第一个
        result_df = result_df.drop_duplicates(subset=['学号'], keep='first')
        print(f"   - 最终有效记录数: {len(result_df)} 条")
        logging.info(f"成功处理作业文件: {os.path.basename(file_path)}, 有效记录数: {len(result_df)}")
        
        return result_df
    
    except Exception as e:
        error_msg = f"读取作业文件失败: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(f"处理作业文件 {os.path.basename(file_path)} 失败: {error_msg}")
        return None

def load_student_list(student_file_path: str) -> pd.DataFrame:
    """
    加载学生名单文件，获取完整的学生基础信息；学生名单格式为教务系统中《学生名单查询》模块导出的Excel文件。
    
    参数:
    student_file_path: str - 学生名单Excel文件路径
    
    返回:
    pd.DataFrame - 包含学号、姓名、班级三列的学生信息
    """
    print(f"\n📋 正在加载学生名单: {os.path.basename(student_file_path)}")
    logging.info(f"开始加载学生名单文件: {os.path.basename(student_file_path)}")
    
    try:
        student_df = pd.read_excel(student_file_path)
    except Exception as e:
        print(f"❌ 读取学生名单失败: {str(e)}")
        logging.error(f"加载学生名单文件 {os.path.basename(student_file_path)} 失败: {str(e)}")
        raise
    
    # 验证学生名单格式
    required_columns = ['学号', '姓名', '班级']
    missing_columns = [col for col in required_columns if col not in student_df.columns]
    if missing_columns:
        error_msg = f"学生名单缺少必要列: {', '.join(missing_columns)}，当前列：{list(student_df.columns)}"
        print(f"❌ {error_msg}")
        logging.error(f"加载学生名单文件 {os.path.basename(student_file_path)} 失败: {error_msg}")
        raise ValueError(error_msg)
    
    # 数据清洗
    # 1. 处理学号为字符串格式
    student_df['学号'] = student_df['学号'].astype(str).str.strip().str.replace(' ', '')
    
    # 2. 去除重复学号
    initial_count = len(student_df)
    student_df = student_df.drop_duplicates(subset=['学号'], keep='first')
    if initial_count > len(student_df):
        print(f"   - 移除重复学号记录: {initial_count - len(student_df)} 条")
        logging.info(f"移除重复学号记录: {initial_count - len(student_df)} 条")
    
    # 3. 去除空值记录
    student_df = student_df.dropna(subset=['学号'])
    
    print(f"   - 总学生人数: {len(student_df)} 人")
    logging.info(f"成功加载学生名单文件: {os.path.basename(student_file_path)}, 总学生人数: {len(student_df)}")
    
    return student_df[required_columns]  # 确保只返回需要的列

def process_exam_score_file(file_path: str, exam_name: str = "笔试") -> Optional[pd.DataFrame]:
    """
    处理笔试成绩文件，提取学号和对应笔试分数
    
    参数:
    file_path: str - 笔试成绩Excel文件的完整路径
    exam_name: str - 考试名称标识（默认为"笔试"）
    
    返回:
    pd.DataFrame - 包含两列：学号、[考试名称]分数；若处理失败返回None
    """
    print(f"🔍 正在解析笔试成绩文件: {os.path.basename(file_path)}")
    logging.info(f"开始处理笔试成绩文件: {os.path.basename(file_path)}")
    
    try:
        # 读取笔试成绩文件
        df = pd.read_excel(file_path)
        
        # 验证文件格式，确保包含必要的列
        required_columns = ['学号', '成绩']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"笔试成绩文件缺少必要列: {', '.join(missing_columns)}，当前列：{list(df.columns)}"
            print(f"❌ {error_msg}")
            logging.error(f"处理笔试成绩文件 {os.path.basename(file_path)} 失败: {error_msg}")
            return None
        
        result_df = df[['学号', '成绩']].copy()
        result_df.columns = ['学号', f'{exam_name}分数']
        
        # ------------------- 数据清洗流程 -------------------
        # 1. 去除学号为空的行
        initial_count = len(result_df)
        result_df = result_df.dropna(subset=['学号'])
        print(f"   - 移除空学号记录: {initial_count - len(result_df)} 条")
        
        # 2. 处理学号数据类型，确保为字符串格式（避免数字型学号丢失前导零）
        result_df['学号'] = result_df['学号'].astype(str)
        # 清理学号中的特殊字符和空格
        result_df['学号'] = result_df['学号'].str.strip().str.replace(' ', '')
        
        # 3. 处理分数数据
        def clean_score(score) -> float:
            """清理分数数据，非数值型或空值返回0"""
            if pd.isna(score):
                return 0.0
            try:
                # 处理可能包含的百分号或其他字符
                score_str = str(score).strip().replace('%', '')
                return float(score_str)
            except (ValueError, TypeError):
                return 0.0
        
        result_df[f'{exam_name}分数'] = result_df[f'{exam_name}分数'].apply(clean_score)
        
        # 4. 去除重复的学号记录，保留第一个
        result_df = result_df.drop_duplicates(subset=['学号'], keep='first')
        print(f"   - 最终有效记录数: {len(result_df)} 条")
        logging.info(f"成功处理笔试成绩文件: {os.path.basename(file_path)}, 有效记录数: {len(result_df)}")
        
        return result_df
    
    except Exception as e:
        error_msg = f"读取笔试成绩文件失败: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(f"处理笔试成绩文件 {os.path.basename(file_path)} 失败: {error_msg}")
        return None

def merge_student_scores(student_df: pd.DataFrame, homework_results: List[pd.DataFrame]) -> pd.DataFrame:
    """
    合并学生基础信息和所有作业成绩
    
    参数:
    student_df: pd.DataFrame - 学生基础信息
    homework_results: List[pd.DataFrame] - 各作业成绩DataFrame列表
    
    返回:
    pd.DataFrame - 合并后的完整成绩表
    """
    print(f"\n🔗 开始合并学生信息和作业成绩")
    logging.info(f"开始合并学生信息和作业成绩，共 {len(homework_results)} 项成绩数据")
    
    # 初始化最终结果为学生基础信息
    final_df = student_df.copy()
    
    # 逐个合并作业成绩
    for homework_df in homework_results:
        # 获取当前作业名称（从列名推断）
        score_col = [col for col in homework_df.columns if col.endswith('分数')][0]
        homework_name = score_col.replace('分数', '')
        
        # 左连接合并，确保所有学生都在结果中
        merge_count_before = len(final_df)
        final_df = pd.merge(final_df, homework_df, on='学号', how='left')
        
        # 填充未找到的作业分数为0（表示未交或无成绩）
        final_df[score_col] = final_df[score_col].fillna(0.0)
        
        # 统计有成绩的学生数
        has_score_count = len(final_df[final_df[score_col] > 0])
        print(f"   - {homework_name}: 有成绩人数 {has_score_count}/{len(final_df)}")
        logging.info(f"合并 {homework_name} 成绩，有成绩人数 {has_score_count}/{len(final_df)}")
    
    # 调整列顺序：基础信息在前，作业分数在后
    base_columns = ['学号', '姓名', '班级']
    score_columns = [col for col in final_df.columns if col.endswith('分数')]
    final_df = final_df[base_columns + score_columns]
    
    print(f"✅ 合并完成，最终成绩表包含 {len(final_df)} 名学生，{len(score_columns)} 项作业")
    logging.info(f"合并完成，最终成绩表包含 {len(final_df)} 名学生，{len(score_columns)} 项作业")
    
    return final_df

def load_group_list(group_file_path: str) -> pd.DataFrame:
    """
    加载分组名单文件
    
    参数:
    group_file_path: str - 分组名单Excel文件路径
    
    返回:
    pd.DataFrame - 包含分组信息的数据框
    """
    print(f"\n📋 正在加载分组名单: {os.path.basename(group_file_path)}")
    logging.info(f"开始加载分组名单文件: {os.path.basename(group_file_path)}")
    
    try:
        # 读取分组名单文件
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
        
        print(f"   - 总组数: {len(df)} 组")
        logging.info(f"成功加载分组名单文件: {os.path.basename(group_file_path)}, 总组数: {len(df)}")
        
        return df
    
    except Exception as e:
        print(f"❌ 读取分组名单失败: {str(e)}")
        logging.error(f"加载分组名单文件 {os.path.basename(group_file_path)} 失败: {str(e)}")
        raise

def adjust_scores_by_group(final_df: pd.DataFrame, group_df: pd.DataFrame) -> pd.DataFrame:
    """
    根据分组名单调整成绩：项目经理的成绩覆盖到成员的相应成绩
    
    参数:
    final_df: pd.DataFrame - 完整成绩表
    group_df: pd.DataFrame - 分组名单
    
    返回:
    pd.DataFrame - 调整后的成绩表
    """
    print(f"\n🔄 正在根据分组名单调整成绩")
    logging.info(f"开始根据分组名单调整成绩，总组数: {len(group_df)}")
    
    # 创建成绩表的副本，避免修改原数据
    adjusted_df = final_df.copy()
    
    # 获取所有分数列
    score_columns = [col for col in adjusted_df.columns if col.endswith('分数')]
    
    # 统计调整的次数
    adjust_count = 0
    
    # 遍历每组
    for _, row in group_df.iterrows():
        project_manager_id = row['项目经理学号']
        members = [row['成员1学号'], row['成员2学号'], row['成员3学号'], row['成员4学号']]
        
        # 跳过项目经理学号为空的组
        if not project_manager_id:
            continue
        
        # 查找项目经理的成绩
        pm_mask = adjusted_df['学号'] == project_manager_id
        if not pm_mask.any():
            print(f"   - 警告：未找到项目经理 {project_manager_id} 的成绩")
            logging.warning(f"未找到项目经理 {project_manager_id} 的成绩")
            continue
        
        # 获取项目经理的成绩
        pm_scores = adjusted_df.loc[pm_mask, score_columns].iloc[0]
        
        # 遍历每个成员
        for member_id in members:
            # 跳过空学号的成员
            if not member_id:
                continue
            
            # 查找成员的记录
            member_mask = adjusted_df['学号'] == member_id
            if not member_mask.any():
                print(f"   - 警告：未找到成员 {member_id} 的记录")
                logging.warning(f"未找到成员 {member_id} 的记录")
                continue
            
            # 使用项目经理的成绩覆盖成员的成绩 - 修正版本
            # 将pm_scores转换为numpy数组或列表，确保正确赋值
            for col in score_columns:
                adjusted_df.loc[member_mask, col] = pm_scores[col]
            
            adjust_count += 1
            
    print(f"✅ 成绩调整完成，共调整 {adjust_count} 条记录")
    logging.info(f"成绩调整完成，共调整 {adjust_count} 条记录")
    
    return adjusted_df

def generate_score_statistics(final_df: pd.DataFrame) -> None:
    """
    生成成绩统计信息并打印
    
    参数:
    final_df: pd.DataFrame - 完整成绩表
    """
    print(f"\n📊 作业成绩统计汇总")
    print("-" * 60)
    logging.info(f"开始生成成绩统计信息")
    
    # 获取所有作业分数列
    score_columns = [col for col in final_df.columns if col.endswith('分数')]
    
    for col in score_columns:
        homework_name = col.replace('分数', '')
        scores = final_df[col]
        
        # 计算统计指标
        stats = {
            '平均分': scores.mean(),
            '最高分': scores.max(),
            '最低分': scores.min(),
            '未交人数': len(scores[scores == 0]),
            '及格人数': len(scores[scores >= 60]),
            '优秀人数': len(scores[scores >= 90])  # 90分以上为优秀
        }
        
        # 打印统计结果
        print(f"{homework_name}:")
        print(f"  平均分: {stats['平均分']:.2f} | 最高分: {stats['最高分']:.0f} | 最低分: {stats['最低分']:.0f}")
        print(f"  未交: {stats['未交人数']}人 | 及格: {stats['及格人数']}人 | 优秀: {stats['优秀人数']}人")
        print(f"  及格率: {stats['及格人数']/len(scores)*100:.1f}% | 优秀率: {stats['优秀人数']/len(scores)*100:.1f}%")
        print()
        
        logging.info(f"{homework_name}统计: 平均分={stats['平均分']:.2f}, 最高分={stats['最高分']:.0f}, 最低分={stats['最低分']:.0f}, 未交人数={stats['未交人数']}, 及格人数={stats['及格人数']}, 优秀人数={stats['优秀人数']}")
    
    print("-" * 60)
    logging.info(f"成绩统计信息生成完成")

def save_to_excel(final_df: pd.DataFrame, output_file_path: str = "学生作业成绩汇总.xlsx") -> None:
    """
    将最终成绩表保存为Excel文件，并设置格式
    
    参数:
    final_df: pd.DataFrame - 完整成绩表
    output_file_path: str - 输出文件路径
    """
    print(f"💾 正在保存成绩表到: {output_file_path}")
    logging.info(f"开始保存成绩表到: {output_file_path}")
    
    try:
        # 使用ExcelWriter设置格式
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='成绩汇总', index=False)
            
            # 获取工作表对象
            worksheet = writer.sheets['成绩汇总']
            
            # 设置列宽（根据内容调整）
            column_widths = {
                'A': 15,  # 学号
                'B': 10,  # 姓名
                'C': 15,  # 班级
            }
            
            # 为作业分数列设置统一宽度
            score_columns_count = len([col for col in final_df.columns if col.endswith('分数')])
            for i in range(score_columns_count):
                col_letter = chr(ord('D') + i)  # D, E, F...
                column_widths[col_letter] = 12
            
            # 应用列宽设置
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
        
        print(f"✅ 保存成功！文件大小: {os.path.getsize(output_file_path)/1024:.1f} KB")
        logging.info(f"成功保存成绩表到: {output_file_path}，文件大小: {os.path.getsize(output_file_path)/1024:.1f} KB")
    
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")
        logging.error(f"保存文件失败: {str(e)}")
        raise

def main():
    """
    主程序入口
    """
    print("=" * 70)
    print("          学生作业成绩汇总系统          ")
    print("=" * 70)
    logging.info("学生作业成绩汇总系统开始运行")
    
    # ------------------- 命令行参数解析 -------------------
    parser = argparse.ArgumentParser(description='学生作业成绩汇总系统')
    parser.add_argument('--data-dir', type=str, default='', help='数据目录路径，默认为当前目录')
    args = parser.parse_args()
    
    # 确定数据目录
    data_dir = args.data_dir if args.data_dir else os.getcwd()

    #测试
    #data_dir = "spm-practice-25秋-软件22"
    print(f"📁 数据目录: {data_dir}")
    logging.info(f"使用数据目录: {data_dir}")
    
    # ------------------- 配置区域 -------------------
    # 从config.json文件读取配置
    try:
        config_path = os.path.join(data_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 从配置中读取文件路径，并与数据目录结合
        STUDENT_FILE_PATH = os.path.join(data_dir, config['STUDENT_FILE_PATH'])
        HOMEWORK_CONFIG = [(os.path.join(data_dir, file_path), homework_name) for file_path, homework_name in config['HOMEWORK_CONFIG']]
        
        # 处理笔试成绩文件路径，为空时不处理
        EXAM_SCORE_PATH = None
        if config.get('EXAM_SCORE_PATH'):
            EXAM_SCORE_PATH = os.path.join(data_dir, config['EXAM_SCORE_PATH'])  # 笔试成绩文件路径
        
        OUTPUT_FILE_PATH = os.path.join(data_dir, config['OUTPUT_FILE_PATH'])  # 输出文件路径
        
        # 检查是否有分组名单配置
        GROUP_LIST_PATH = None
        if 'GROUP_LIST_PATH' in config and config['GROUP_LIST_PATH']:
            GROUP_LIST_PATH = os.path.join(data_dir, config['GROUP_LIST_PATH'])
        
        print(f"📁 配置文件加载成功: config.json")
        print(f"   - 学生名单文件: {os.path.basename(STUDENT_FILE_PATH)}")
        print(f"   - 作业文件数量: {len(HOMEWORK_CONFIG)}")
        if EXAM_SCORE_PATH:
            print(f"   - 笔试成绩文件: {os.path.basename(EXAM_SCORE_PATH)}")
        else:
            print(f"   - 笔试成绩文件: 未配置")
        print(f"   - 输出文件: {os.path.basename(OUTPUT_FILE_PATH)}")
        if GROUP_LIST_PATH:
            print(f"   - 分组名单文件: {os.path.basename(GROUP_LIST_PATH)}")
        
        logging.info(f"配置文件加载成功，学生名单文件: {os.path.basename(STUDENT_FILE_PATH)}, 作业文件数量: {len(HOMEWORK_CONFIG)}, 输出文件: {os.path.basename(OUTPUT_FILE_PATH)}")
        if EXAM_SCORE_PATH:
            logging.info(f"笔试成绩文件: {os.path.basename(EXAM_SCORE_PATH)}")
        else:
            logging.info(f"笔试成绩文件: 未配置")
        if GROUP_LIST_PATH:
            logging.info(f"分组名单文件: {os.path.basename(GROUP_LIST_PATH)}")
        
    except FileNotFoundError:
        print(f"❌ 配置文件 config.json 未找到")
        logging.error(f"配置文件 config.json 未找到")
        exit(1)
    except KeyError as e:
        print(f"❌ 配置文件格式错误，缺少必要字段: {e}")
        logging.error(f"配置文件格式错误，缺少必要字段: {e}")
        exit(1)
    except json.JSONDecodeError:
        print(f"❌ 配置文件格式错误，不是有效的JSON格式")
        logging.error(f"配置文件格式错误，不是有效的JSON格式")
        exit(1)
    
    # ------------------- 执行流程 -------------------
    try:
        # 1. 加载学生名单
        student_df = load_student_list(STUDENT_FILE_PATH)
        
        # 2. 处理所有作业文件
        homework_results = []
        for file_path, homework_name in HOMEWORK_CONFIG:
            homework_df = process_homework_file(file_path, homework_name)
            if homework_df is not None:
                homework_results.append(homework_df)
            else:
                print(f"   - 跳过处理失败的作业文件: {os.path.basename(file_path)}")
        
        # 3. 处理笔试成绩文件（如果配置了）
        if EXAM_SCORE_PATH:
            exam_df = process_exam_score_file(EXAM_SCORE_PATH)
            if exam_df is not None:
                homework_results.append(exam_df)
            else:
                print(f"   - 跳过处理失败的笔试成绩文件")
        else:
            print(f"   - 笔试成绩文件未配置，跳过处理")
        
        # 4. 合并学生信息和所有成绩（包括作业和笔试）
        if homework_results:
            final_score_df = merge_student_scores(student_df, homework_results)
            
            # 5. 如果有分组名单，调整成绩
            if GROUP_LIST_PATH and os.path.exists(GROUP_LIST_PATH):
                group_df = load_group_list(GROUP_LIST_PATH)
                final_score_df = adjust_scores_by_group(final_score_df, group_df)
            elif GROUP_LIST_PATH:
                print(f"   - 分组名单文件不存在: {os.path.basename(GROUP_LIST_PATH)}")
                logging.warning(f"分组名单文件不存在: {os.path.basename(GROUP_LIST_PATH)}")
            
            # 6. 生成成绩统计
            generate_score_statistics(final_score_df)
            
            # 7. 保存结果到Excel
            save_to_excel(final_score_df, OUTPUT_FILE_PATH)
            
            # 8. 显示最终结果预览
            print(f"\n📄 最终成绩表预览（前5行）:")
            print(final_score_df.head().to_string(index=False))
            
            print(f"\n" + "=" * 70)
            print("          程序执行完成！          ")
            print(f"📁 输出文件: {os.path.abspath(OUTPUT_FILE_PATH)}")
            print("=" * 70)
            logging.info(f"程序执行完成，输出文件: {os.path.abspath(OUTPUT_FILE_PATH)}")
        else:
            print(f"\n❌ 没有成功处理的作业或笔试成绩文件，无法生成汇总表")
            logging.error(f"没有成功处理的作业或笔试成绩文件，无法生成汇总表")
            exit(1)
    
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        print("请检查：1.文件路径是否正确 2.文件格式是否符合要求 3.是否有读取权限")
        logging.error(f"程序执行出错: {str(e)}")
        exit(1)

# ------------------- 扩展说明 -------------------
"""
扩展新作业的步骤：
1. 准备新的作业Excel文件（格式需与现有作业文件一致）
2. 在config.json文件的HOMEWORK_CONFIG数组中添加新的配置项：
   ["新作业文件路径.xlsx", "新作业名称"]
3. 直接运行程序，系统会自动处理新作业并添加到成绩表中

添加新考试成绩（如笔试、实验考试等）：
1. 准备新的考试成绩Excel文件，确保包含"学号"和"成绩"列
2. 在config.json文件中添加或修改EXAM_SCORE_PATH配置项
3. 如需添加多个考试成绩，可修改process_exam_score_file函数和main函数

添加分组名单功能：
1. 准备分组名单Excel文件，包含6列：题目，项目经理学号，成员1学号，成员2学号，成员3学号，成员4学号
2. 在config.json文件中添加GROUP_LIST_PATH配置项：
   "GROUP_LIST_PATH": "分组名单.xlsx"
3. 直接运行程序，系统会自动根据分组名单调整成绩

常见问题解决：
Q1: 作业分数读取错误？
A1: 检查作业文件格式，确保分数在第九列（索引8），若格式变化需调整process_homework_file中的列索引

Q2: 学生学号无法匹配？
A2: 检查学号格式是否一致，程序已将学号统一处理为字符串格式，确保无特殊字符

Q3: 中文文件名乱码？
A3: 确保运行环境支持中文编码，或使用英文文件名
"""

# 程序入口
if __name__ == "__main__":
    main()