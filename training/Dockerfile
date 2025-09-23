# training/Dockerfile (GPU ready)
# 使用 NVIDIA CUDA 12.8 runtime + Python 3.12
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04

# 基本依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgomp1 \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 common 並安裝 (editable mode)
COPY common/ /app/common
# RUN pip3 install --upgrade pip
# RUN pip3 install -e /app/common

RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -e /app/common

# 複製 training 程式碼
COPY training/ /app/training

# 安裝 training requirements
WORKDIR /app/training
RUN pip3 install --no-cache-dir -r requirements.txt

# 回到工作目錄
WORKDIR /app

# 預設啟動指令
CMD ["python3", "training/train.py"]

