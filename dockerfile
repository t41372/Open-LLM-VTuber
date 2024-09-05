# Base image
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu22.04 AS base

# Set noninteractive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential libsndfile1 \
    git \
    curl \
    ffmpeg \
    libportaudio2 \
    g++ \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm get-pip.py

# Copy requirements and install common dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install common Python packages
RUN pip install -U funasr modelscope huggingface_hub
RUN pip install pywhispercpp
RUN pip install torch torchaudio
RUN pip install edge-tts azure-cognitiveservices-speech py3-tts

# MeloTTS installation
WORKDIR /opt/MeloTTS
RUN git clone https://github.com/myshell-ai/MeloTTS.git /opt/MeloTTS
RUN pip install -e .
RUN python -m unidic download
RUN python melo/init_downloads.py

# Whisper variant
FROM base AS whisper
ARG INSTALL_ORIGINAL_WHISPER=false
RUN if [ "$INSTALL_WHISPER" = "true" ]; then \
        pip install openai-whisper; \
    fi

# Bark variant
FROM whisper AS bark
ARG INSTALL_BARK=false
RUN if [ "$INSTALL_BARK" = "true" ]; then \
        pip install git+https://github.com/suno-ai/bark.git; \
    fi

# Final image
FROM bark AS final

# Copy application code to the container
COPY . /app

# Set working directory
WORKDIR /app

# Expose port 12393 (the new default port)
EXPOSE 12393

CMD ["python3", "server.py"]