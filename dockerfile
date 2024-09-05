FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04

# Set noninteractive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
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

# Install pip for the pre-installed Python 3.12
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm get-pip.py

# Copy requirements and install dependencies
COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install additional Python packages
RUN pip install edge-tts azure-cognitiveservices-speech
RUN pip install git+https://github.com/suno-ai/bark.git
RUN pip install pywhispercpp openai-whisper

# Copy application code to the container
COPY . /app

# Set working directory
WORKDIR /app

# Expose port 12393 (the new default port)
EXPOSE 12393

CMD ["python3", "server.py"]
