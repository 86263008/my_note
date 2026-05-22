# 操作步骤

1. 使用*venv*创建虚拟环境目录`.venv`

```sh
py -m venv .venv
```

2. 激活虚拟环境：

```sh
.venv\scripts\activate
cd web
```

3. 安装依赖（首次）

```sh
pip install -r requirements.txt
```

4. Pdf转Word

```sh
py pdf_to_word.py pdf/1.pdf pdf_out/1.docx 
```