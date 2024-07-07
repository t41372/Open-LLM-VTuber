# 使用NVIDIA CUDA基礎映像
FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

# 設定非交互式安裝，避免安裝過程中出現提示
ENV DEBIAN_FRONTEND=noninteractive

# 更新並安裝基本工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    git \
    curl \
    ffmpeg \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install g++ -y --no-install-recommends

# 複製requirements.txt到容器中
COPY requirements.txt /tmp/

# 安裝Python依賴
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN pip3 install edge-tts azure-cognitiveservices-speech
RUN pip3 install git+https://github.com/suno-ai/bark.git
RUN pip3 install pywhispercpp openai-whisper

# 複製項目文件到容器中
COPY . /app

# 設定工作目錄
WORKDIR /app

# 預設命令
CMD ["python3", "launch.py"]