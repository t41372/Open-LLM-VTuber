
FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04


ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-distutils \
    python3.11-dev \
    git \
    curl \
    ffmpeg \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install g++ -y --no-install-recommends


RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.11 get-pip.py && rm get-pip.py


COPY requirements.txt /tmp/

RUN pip3.11 install --no-cache-dir -r /tmp/requirements.txt
RUN pip3.11 install edge-tts azure-cognitiveservices-speech
RUN pip3.11 install git+https://github.com/suno-ai/bark.git
RUN pip3.11 install pywhispercpp openai-whisper

COPY . /app

WORKDIR /app

EXPOSE 8000

# You need to run the server.py file AND the launch.py for now, so you will need to get into the container and execute `python launch.py` by yourself. lol
CMD ["python3.11", "server.py"]
