# 使用 Python 3.9 作為基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製必要文件
COPY requirements.txt .
COPY app.py .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Streamlit 默認端口
EXPOSE 8501

# 設置啟動命令
CMD ["streamlit", "run", "app.py"] 