在Windows平台上使用John the Ripper（John）的操作流程与Linux略有不同，主要体现在工具获取、路径处理和命令执行方式上。以下是针对Windows系统的详细使用指南（以破解ZIP文件密码为例，**确保操作对象为合法授权的文件**）：


### 一、Windows平台安装与准备
#### 1. 下载John the Ripper
- 访问官方地址：从官方官方仓库的Windows版本页面下载「John the Ripper 1.9.x for Windows」（推荐「john-1.9.0-jumbo-1-win64.zip」64位版本）。
- 解压文件：将下载的ZIP包解压到任意路径（如`C:\John`），解压后会看到`run`文件夹（核心工具所在目录，包含`john.exe`、`zip2john.exe`等）。


#### 2. 准备目标文件和字典

- 目标文件：准备一个加密的ZIP文件（如`test.zip`），建议放在`C:\John\run`目录下（简化路径操作）。
- 密码字典（可选）：下载或创建一个密码字典文件（如`passwords.txt`，包含常见密码，如`123456`、`password`等），也放在`run`目录下。


### 二、Windows命令行操作步骤

#### 步骤1：打开命令提示符（CMD）并进入John的运行目录
1. 按下`Win + R`，输入`cmd`，打开命令提示符。
2. 进入John的`run`目录（根据实际解压路径调整）：

   ```bash
   cd D:\WS_Edu\my-notes\mkdocs_notes\my-note\docs\tool\John the Ripper\john-1.9.0-jumbo-1-win64\run
   ```

#### 步骤2：提取ZIP文件的密码哈希
使用`zip2john.exe`工具提取加密ZIP的密码哈希（哈希是密码的加密形式，John实际破解的是哈希）：
```bash
zip2john.exe ""D:\WS_Edu\my-notes\mkdocs_notes\my-note\docs\tool\John the Ripper\大道段永平投资问答录 (赵理亚(选).pdf"" > zip_hash.txt
```
- 说明：  
  - `test.zip`是你的加密ZIP文件名（若不在`run`目录下，需写完整路径，如`C:\Users\YourName\test.zip`）。  
  - `> zip_hash.txt`表示将提取的哈希信息保存到`zip_hash.txt`文件中。  
- 执行成功后，`run`目录会生成`zip_hash.txt`。


#### 步骤3：使用John破解哈希

根据密码线索选择攻击模式（以下为常用方式）：

##### 模式1：字典攻击（推荐，速度最快）
如果有密码字典（如`passwords.txt`），优先使用字典攻击：
```bash
john.exe --wordlist=passwords.txt zip_hash.txt
```
- 若字典中包含正确密码，John会快速显示结果（如`123456`）。


##### 模式2：暴力攻击（无密码线索时）
若没有字典，John会默认使用内置字符集（数字、大小写字母、特殊符号）进行暴力破解：
```bash
john.exe zip_hash.txt
```
- 注意：暴力攻击速度较慢，复杂密码可能需要数小时至数天。

##### 模式3：掩码攻击（已知部分密码结构）
如果知道密码的部分特征（如长度、前缀、字符类型），可使用掩码攻击提高效率。例如：  
- 已知密码是6位纯数字：
  ```bash
  john.exe --mask=?????? --charset=?d zip_hash.txt
  ```
- 已知密码是8位，前2位是大写字母，后6位是数字：
  ```bash
  john.exe --mask=?u?u?????? --charset=?u?d zip_hash.txt
  ```
- 掩码规则：`?l`=小写字母，`?u`=大写字母，`?d`=数字，`?s`=特殊符号，`?a`=所有字符。


#### 步骤4：查看破解结果
破解成功后，用以下命令查看密码：
```bash
john.exe --show zip_hash.txt
```
- 输出示例：  
  `test.zip:$zip$1*...*123456::test.zip`  
  其中`123456`即为破解出的密码。


### 三、Windows平台实用技巧
1. **暂停与恢复破解**：  
   破解过程中按`Ctrl + C`暂停，再次运行`john.exe zip_hash.txt`会自动恢复进度（John会保存临时进度到`john.pot`文件）。

2. **指定密码长度范围**：  
   若已知密码长度（如6-8位），可限制范围加速破解：
   ```bash
   john.exe --min-length=6 --max-length=8 zip_hash.txt
   ```

3. **使用图形化界面（可选）**：  
   若不习惯命令行，可安装「Johnny」（John的图形化前端），下载地址：[Johnny官方页面](https://openwall.info/wiki/john/johnny)，操作更直观。


### 四、注意事项
1. **路径问题**：Windows中文件路径若包含空格，需用双引号包裹（如`zip2john.exe "C:\My Files\test.zip" > zip_hash.txt`）。
2. **杀毒软件误报**：John可能被部分杀毒软件识别为“可疑程序”，可暂时关闭实时防护（确保从官方渠道下载）。
3. **合法性**：仅可用于自己拥有权限的文件，未经授权破解他人加密文件涉嫌违法。

通过以上步骤，即可在Windows平台使用John the Ripper完成基本的密码破解操作。实际使用中，建议优先收集密码线索（如长度、常用字符），并配合合适的字典以提高效率。