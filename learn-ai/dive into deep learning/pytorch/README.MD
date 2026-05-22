## 创建虚拟环境

```bash
py -m venv .venv
```

## 激活虚拟环境

```bash
.venv\Scripts\activate
```

## 反激活虚拟环境

```bash
.venv\Scripts\deactivate
```

## 安装依赖

**安装 PyTorch**

```bash
pip install numpy matplotlib pandas requests torch torchvision
```

**安装 d2l**

```bash
pip install d2l
```

## 导出当前环境

```bash
pip freeze > requirements.txt
```
