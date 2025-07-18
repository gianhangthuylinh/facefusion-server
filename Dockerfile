FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG FACEFUSION_VERSION=3.3.2
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    SHELL=/bin/bash

# Cài đặt các gói hệ thống cần thiết
RUN apt update && \
    apt -y upgrade && \
    apt install -y --no-install-recommends \
        python3.10-venv \
        python3-pip \
        python3-tk \
        python3-dev \
        git \
        curl \
        ffmpeg \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Cài đặt FaceFusion
WORKDIR /facefusion
RUN git clone https://github.com/facefusion/facefusion.git --branch ${FACEFUSION_VERSION} --single-branch .
RUN python install.py --onnxruntime cuda --skip-conda

# Thiết lập thư mục làm việc cho API
WORKDIR /app

# Sao chép và cài đặt dependencies cho API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn API
COPY ./app ./app

# Tạo các thư mục cần thiết
RUN mkdir -p /app/uploads /app/results && \
    chmod 755 /app/uploads /app/results

# Thiết lập biến môi trường cho API
ENV PYTHONPATH=/app:/facefusion
ENV FACEFUSION_PATH=/facefusion

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Khởi chạy API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]