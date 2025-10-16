import csv
import datetime
import json
from playwright.sync_api import sync_playwright, Page, BrowserContext, PlaywrightContextManager
import re
import time
import tkinter as tk
from tkinter import simpledialog

import EmailSender
from LearnConfig import LearnConfig

def extract_courses(page: Page):
  """从网页中提取课程信息
  
  功能：从指定网页中提取所有课程的名称、链接和学时信息
  
  参数：
      page: Playwright的Page对象，代表要提取信息的网页
  
  返回值：
      dict: 包含课程信息的字典，键为课程名称，值为包含课程详细信息的子字典
            每个子字典包含以下键值对：
            - 'h2_text': 课程名称
            - 'link': 课程链接的Playwright元素对象
            - 'hours': 课程学时（如果无法提取则为None）
  """

  result_dict = {}
  # 获取课程框
  news_containers = page.locator('li.clearfix').all()
  
  # 用于匹配"需认定X学时"格式的正则表达式
  hours_pattern = re.compile(r'需认定(\d+)学时')
  
  # 遍历每个新闻容器
  for container in news_containers:
    # 获取课程链接
    a_elements = container.locator('a').all()
    
    # 提取需认定学时
    news_time = container.locator('div.news_time').first
    child_elements = news_time.locator("*")
    count = child_elements.count()
    hours = 2
    for i in range(count):
        element = child_elements.nth(i)
        text = element.text_content() or ""
        hours_match = hours_pattern.search(text)
        hours = hours_match.group(1) if hours_match else None
        if hours:
            break
    
    # 提取课程信息
    for a in a_elements:
      # 获取课程名称
      h2_element = a.locator('h2').first
      if h2_element.count() > 0:
        h2_text = h2_element.text_content()
        if h2_text:
          h2_text = h2_text.strip()
          
          # 将信息添加到字典
          result_dict[h2_text] = {
              'course_name': h2_text, # 课程名称
              'link': a, # 课程链接
              'hours': hours  # 课程学时
          }
  
  return result_dict


def monitor_tab(page: Page) -> bool:
    """监控标签页并处理弹窗确认按钮
    
    功能：搜索标签页面内的确认按钮并点击，提取当前播放视频信息并记录到CSV文件
    
    参数：
        page: Playwright的Page对象，代表要监控的浏览器标签页
        tab_index: 标签页索引，用于日志记录和错误提示
    
    返回值：
        bool: 如果成功找到并点击了确认按钮，返回True；否则返回False
    """

    try:
        file_exists = False
        learn_rec_file = "learn_rec.csv"
        try:
            with open(learn_rec_file, 'r', encoding='utf-8') as f:
                file_exists = True
        except FileNotFoundError:
            pass

        # 查找类为layui-layer-btn0且文本为"确定"的元素
        confirm_button = page.locator(
            '//a[contains(@class, "layui-layer-btn0") and text()="确定"]'
        )
        
        # 检查元素是否可见且可点击
        if confirm_button.is_visible() and confirm_button.is_enabled():
            # 提取当前播放视频的标题和时长
            video_div = page.locator('div.video-title.clearfix.on')
            video_div.wait_for() 
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 当前时间
            title = video_div.locator('span.two').text_content()
            duration = video_div.locator('span.three').text_content()
            title = title.strip() if title else "未获取到标题"
            duration = duration.strip() if duration else "未获取到时长"
            
            confirm_button.click()
            # 写入CSV文件
            with open("learn_rec.csv", 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 如果是新文件，先写入表头
                if not file_exists:
                    writer.writerow(["记录时间", "视频标题", "视频时长"])
                # 写入数据行
                writer.writerow([current_time, title, duration])

            print(f"{current_time} | {title} | {duration} 已学习！")
            
            return True
    except Exception as e:
        print(f"监控标签页 {page.title()} 时发生异常: {e}")
    return False

def get_timeout(default_minutes=90):
    """获取用户输入的超时时间，使用Tkinter对话框
    
    参数：
        default_minutes: 默认超时分钟数，默认为90分钟
    
    返回值：
        int: 用户输入的超时分钟数（如果超时或取消则返回默认值）
    """
    
    # 创建根窗口并隐藏
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 确保对话框置顶
    
    # 初始化结果变量
    result = [default_minutes]  # 默认值
    dialog_shown = [False]  # 标记对话框是否已显示
    
    # 定义超时处理函数
    def timeout_handler():
        print(f"超时提示：输入超时，已使用默认超时时间：{default_minutes}分钟")
        root.destroy()
    
    try:
        # 安排超时检查（60秒后）
        root.after(10000, timeout_handler)  # 60000毫秒 = 60秒
        
        # 显示输入对话框，设置默认值
        dialog_shown[0] = True
        user_input = simpledialog.askstring(
            title="设置学习监控超时时间",
            prompt=f"请输入监控超时时间（分钟），默认为{default_minutes}分钟：",
            initialvalue=str(default_minutes)  # 填入默认值
        )
        
        # 取消超时处理
        root.after_cancel(timeout_handler)  # 这行可能会报错，但不影响功能
        
        # 处理用户输入
        if user_input is None:  # 用户点击了取消或关闭
            result[0] = default_minutes
            print(f"提示：已使用默认超时时间：{default_minutes}分钟")
        else:
            # 验证输入是否为正整数
            if user_input.strip().isdigit() and int(user_input) > 0:
                result[0] = int(user_input)
                print(f"设置成功：学习监控超时时间已设置为：{result[0]}分钟")
            else:
                result[0] = default_minutes
                print(f"输入错误：请输入有效的正整数！已使用默认值。")
    except Exception as e:
        print(f"获取超时时间时发生异常: {e}")
        result[0] = default_minutes
    finally:
        # 确保关闭根窗口
        try:
            root.destroy()
        except:
            pass
    
    return result[0]


def open_homepage(p: PlaywrightContextManager, url: str, config: LearnConfig):
    """打开指定URL的首页
    
    参数:
        url (str): 要打开的首页URL地址
        config (LearnConfig): 学习监控配置对象，包含学习参数设置
    
    返回值:
        context: Playwright Chromium浏览器上下文对象
    """
    
    # 启动指定路径的Chrome
    context = p.chromium.launch_persistent_context(
        user_data_dir="./chrome_profile",  # 保存浏览器状态的目录
        executable_path=config.chrome_path, #r"C:\Users\jianh\AppData\Local\Google\Chrome\Application\chrome.exe",
        headless=False,  # 以有界面模式运行
        args=["--no-sandbox"]  # 解决部分系统权限问题
    )

    page = context.new_page()
    page.goto(url)
    print(f"已打开初始页面: {url}")
    
    return context
    

def wait_tab(context: BrowserContext, tilte: str) -> Page: 
  """等待指定标题的标签页出现
  
  参数：
      context: Playwright的BrowserContext对象，代表浏览器上下文
      tilte: 导航页面标题字符串
  
  返回值：
      Page: 找到的匹配页面对象；如果未找到则可能陷入无限循环
  """

  nav_page = None

  while True:
    pages = context.pages
    for i, page in enumerate(pages, 1):
      title_i = page.title()
      if tilte == title_i:
        nav_page = page
        print(f"指定标题的标签页出现: {nav_page.title()}")
        break
    if nav_page:
        break
    
  return nav_page


def learn_course(course_page: Page, timeout_minutes: int):
    """学习指定课程页面
    
    参数:
        course_page (Page): Playwright的Page对象，代表课程页面
        title (str): 课程名称，用于打印学习状态
    """
    start_time = time.time()
    title = course_page.title()
    print(f"《{title}》将学习{timeout_minutes}分钟...")
    
    while True:
      elapsed_minutes = (time.time() - start_time) / 60
      # 达到学习时间
      if elapsed_minutes >= timeout_minutes:
          print(f"《{title}》已学习超{timeout_minutes}分钟！")
          break
        
      monitor_tab(course_page)
      time.sleep(1)

def monitor_all_tabs(url, config: LearnConfig):
    """监控指定URL的所有浏览器标签页，自动点击学习平台中的确定按钮并记录学习情况
    
    参数:
        url (str): 要监控的学习平台URL地址
        config (LearnConfig): 学习监控配置对象，包含学习参数设置
    
    功能:
        1. 设置超时监控，超时后发送邮件提醒
        2. 使用Playwright启动Chrome浏览器并保存浏览器状态
        3. 持续监控所有打开的标签页
        4. 对每个活跃标签页调用monitor_tab函数进行处理
        5. 程序异常终止时捕获并显示错误信息
        6. 程序结束时发送完成通知邮件
    """
    
    with sync_playwright() as p:
      context = open_homepage(p, url, config)
      
      nav_page = wait_tab(context, config.nav_title)

      courses = extract_courses(nav_page)

      course_rec = []
      for course_name in courses:
          course = courses[course_name]
          # 打开课程页面
          course["link"].click()
          course_page = wait_tab(context, course["course_name"])
          time.sleep(1)

          # 开始学习
          start_study_link = course_page.locator('a#startStudy')
          start_study_link.click()
          time.sleep(1)

          # 学习
          timeout_minutes = float(course["hours"]) * config.duration_per_class
          learn_course(course_page, timeout_minutes)
          
          # 学习完成
          course_page.close()
          course_rec.append({
              "course_name": course["course_name"],
              "hours": course["hours"],
              "timeout_minutes": timeout_minutes
          })

    # 通知老板，任务完成
    email_sender = EmailSender.EmailSender()
    email_sender.send(
        config.email, 
        "国家智慧教育公共服务平台学习完成", 
        f"已完成学习以下课程：\n{json.dumps(course_rec, ensure_ascii=False, indent=2)}"
    )

if __name__ == "__main__":
    config = LearnConfig()
    target_url = "https://www.smartedu.cn/"  # 替换为实际目标URL
    monitor_all_tabs(target_url, config)