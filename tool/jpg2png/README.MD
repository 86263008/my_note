## 使用步骤

1. 使用*venv*创建虚拟环境目录`.venv`

```shell
py -m venv .venv
```

2. 激活虚拟环境：

```shell
.venv\scripts\activate
cd web
```

3. 安装依赖

```shell
pip install opencv-python pillow numpy
pip install -r requirements.txt
```

4. 导出依赖

```shell
pip freeze > requirements.txt
```