import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

class EmailSender:
    # 将QQ邮箱的SMTP服务器信息作为类的私有成员
    _SMTP_SERVER = "smtp.qq.com"
    _SMTP_PORT = 465
    _USE_SSL = True
    _DEFAULT_CONTENT_TYPE = "html"
    _USER_NAME="86263008@qq.com"
    _PASSWORD="rkkihodpmejdcabh"

    def __init__(self):
        """初始化邮件发送器，使用预设的QQ邮箱SMTP配置"""
        self.smtp_server = self._SMTP_SERVER
        self.smtp_port = self._SMTP_PORT
        self.use_ssl = self._USE_SSL
        self.server = None
        # 初始化实例私有成员
        self._username = self._USER_NAME
        self._password = self._PASSWORD
        self._content_type = self._DEFAULT_CONTENT_TYPE
    
    def _login(self):
        """[私有] 使用存储的用户名和密码登录SMTP服务器"""
        if not self._username or not self._password:
            print("用户名或密码未设置")
            return False
            
        try:
            if self.use_ssl:
                self.server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                self.server.starttls()
            
            self.server.login(self._username, self._password)
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def _send_email(self, receivers, subject, content):
        """[私有] 发送邮件"""
        if not self.server:
            print("请先登录SMTP服务器")
            return False
        
        try:
            # 创建一个带附件的实例
            message = MIMEMultipart()
            message['From'] = Header(self._username)
            message['To'] = Header(", ".join(receivers))
            message['Subject'] = Header(subject)
            
            # 邮件正文内容
            message.attach(MIMEText(content, self._content_type, 'utf-8'))
            
            # 发送邮件
            self.server.sendmail(self._username, receivers, message.as_string())
            print(f"邮件发送成功！发送到: {', '.join(receivers)}")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def _quit(self):
        """[私有] 退出SMTP服务器连接"""
        if self.server:
            self.server.quit()
    
    
    def send(self, receivers,subject=None, content=None):
        """发送邮件的主要接口"""
        
        # 登录服务器
        if not self._login():
            print("登录失败，程序退出")
            print("提示：请确保您已正确获取QQ邮箱授权码，并开启了SMTP服务")
            return False
        
        try:
            receivers = [email.strip() for email in receivers.split(',')]
            
            # 如果没有提供主题和内容，则交互式获取
            if subject is None:
                subject = input("请输入邮件主题: ")
                
            if content is None:
                content = input("请输入邮件内容: ")
            
            # 发送邮件
            return self._send_email(receivers, subject, content)
        finally:
            # 退出连接
            self._quit()
            # 清空敏感信息
            self._password = None


if __name__ == "__main__":
    email_sender = EmailSender()
    email_sender.send("86263008@qq.com", "test", "Hello")