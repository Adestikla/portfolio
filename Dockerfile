# 使用微软官方包含完整系统底层依赖的纯净镜像
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# 优先安装 Python 依赖库
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 把整个项目代码复制进容器
COPY . .

# 暴露给外部访问的端口
EXPOSE 8080

# 启动命令（精确指向 backend 目录下的 main.py）
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]