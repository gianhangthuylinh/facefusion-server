#!/bin/bash

# Script ví dụ để chạy FaceFusion trực tiếp trong Docker container

# Cách sử dụng:
# ./run-command.sh <source_image.jpg> <target_video.mp4> <processor> <output.mp4>

SOURCE=${1:-"elon.jpg"}
TARGET=${2:-"Download.mp4"}
PROCESSOR=${3:-"deep_swapper"}
OUTPUT=${4:-"output/fake_video.mp4"}

# Tạo thư mục output nếu chưa tồn tại
mkdir -p $(dirname "$OUTPUT")

# Chạy Docker container
docker run --gpus all --rm \
  -v "$(pwd)/$SOURCE:/app/source.jpg" \
  -v "$(pwd)/$TARGET:/app/target.mp4" \
  -v "$(pwd)/$(dirname $OUTPUT):/app/output" \
  facefusion-api \
  python3 /facefusion/facefusion.py headless-run \
  -s /app/source.jpg \
  -t /app/target.mp4 \
  --processors $PROCESSOR \
  -o /app/output/$(basename $OUTPUT)

echo "Đã hoàn thành. Video đầu ra: $OUTPUT"
