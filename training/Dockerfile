# training/Dockerfile (GPU ready)
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# 設定 ARG 和 ENV 以便管理 Python 版本，更具彈性
ARG PYTHON_VERSION=3.12
ENV DEBIAN_FRONTEND=noninteractive


# 更新 apt, 加入 deadsnakes PPA 來安裝 Python 3.12, 並安裝必要的系統工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    cmake \
    git \
    curl \
    # 新增 deadsnakes PPA
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    # 從 PPA 安裝指定的 Python 版本及其開發工具
    && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    # 清理 apt 快取
    && rm -rf /var/lib/apt/lists/* \
    # 透過 update-alternatives 建立符號連結 (symlink)，讓 python3 指向 python3.12
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    # --- 為新的 Python 版本安裝 pip ---
    # 使用官方推薦的 get-pip.py 來確保 pip 與 python 版本對應
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION}

# 設定工作目錄
WORKDIR /app

# 複製 common 並安裝 (editable mode)
# 此處不需更動，因為後續的 pip3 指令會自動使用我們設定好的 Python 3.12
COPY common/ /app/common

RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -e /app/common

# 複製 training 程式碼
COPY training/ /app/training

# 安裝 training requirements
WORKDIR /app/training
RUN pip3 install --no-cache-dir --ignore-installed -r requirements.txt

# 回到工作目錄
WORKDIR /app

# 預設啟動指令
# 此處不需更動，CMD 會使用我們設定好的 python3 (也就是 Python 3.12)
CMD ["python3", "training/train.py"]

