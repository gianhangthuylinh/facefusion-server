# facefusion-server
# FaceFusion API

API để swap khuôn mặt sử dụng FaceFusion trên RunPod.

## Cài đặt

### Sử dụng Docker

```bash
docker build -t facefusion-server .
docker run --gpus all -p 7860:7860 facefusion-server
```

### Sử dụng Docker Compose

```bash
docker-compose up -d
```

Hoặc chỉ định phiên bản FaceFusion:

```bash
FACEFUSION_VERSION=3.3.2 docker-compose up -d
```

### Sử dụng trên RunPod

1. Tạo một RunPod với GPU
2. Upload source code này lên
3. Build và chạy Docker container

## API Endpoints

### 1. Swap Face

```
POST /swap
```

**Parameters:**

- `source`: File ảnh khuôn mặt nguồn (required) - hỗ trợ JPG, JPEG, PNG, WEBP, BMP
- `target`: File ảnh hoặc video đích (required) - hỗ trợ JPG, JPEG, PNG, WEBP, BMP cho ảnh; MP4, AVI, MOV, WEBM, MKV, FLV cho video
- `type`: Loại đầu ra, "image" hoặc "video" (default: "image")
- `processor`: Bộ xử lý face swap, ví dụ: "deep_swapper" (default), "blendswap_1", "fast_face_swap", "inswapper", v.v.

**Ví dụ cURL:**

```bash
# Swap ảnh sang ảnh (PNG) sử dụng deep_swapper
curl -X POST http://<your-runpod-url>:7860/swap \
  -F "source=@path/to/source_face.png" \
  -F "target=@path/to/target_image.png" \
  -F "type=image" \
  -F "processor=deep_swapper" \
  -o result.png

# Swap ảnh sang video sử dụng inswapper
curl -X POST http://<your-runpod-url>:7860/swap \
  -F "source=@path/to/source_face.jpg" \
  -F "target=@path/to/target_video.mp4" \
  -F "type=video" \
  -F "processor=inswapper" \
  -o result.mp4
```

**Ví dụ Python:**

```python
import requests

# Swap ảnh sang ảnh (WEBP) sử dụng deep_swapper
files = {
    'source': open('source_face.webp', 'rb'),
    'target': open('target_image.webp', 'rb')
}
data = {
    'type': 'image',
    'processor': 'deep_swapper'
}

response = requests.post('http://<your-runpod-url>:7860/swap', files=files, data=data)

with open('result.webp', 'wb') as f:
    f.write(response.content)

# Swap ảnh sang video sử dụng blendswap_1
files = {
    'source': open('source_face.png', 'rb'),
    'target': open('target_video.mp4', 'rb')
}
data = {
    'type': 'video',
    'processor': 'blendswap_1'
}

response = requests.post('http://<your-runpod-url>:7860/swap', files=files, data=data)

with open('result.mp4', 'wb') as f:
    f.write(response.content)
```

## Định dạng hỗ trợ

### Ảnh nguồn (source)
- JPG/JPEG
- PNG
- WEBP
- BMP

### Ảnh/Video đích (target)
- **Ảnh**: JPG/JPEG, PNG, WEBP, BMP
- **Video**: MP4, AVI, MOV, WEBM, MKV, FLV

### Đầu ra (output)
- **Ảnh**: Định dạng giữ nguyên như file gốc (JPG/JPEG, PNG, WEBP, BMP)
- **Video**: MP4 (H.264 codec)

## Sử dụng với Runpod

1. Đăng ký tài khoản tại [RunPod](https://console.runpod.io/)
2. Chọn một Pod với GPU (khuyến nghị tối thiểu 8GB VRAM)
3. Deploy code này theo hướng dẫn cài đặt
4. Gọi API thông qua URL được cung cấp bởi RunPod

## Notes

- API sử dụng FaceFusion để hoán đổi khuôn mặt
- Cần GPU để xử lý hiệu quả (khuyến nghị NVIDIA GPU)
- Xử lý video có thể mất nhiều thời gian hơn, tuỳ thuộc vào độ dài và độ phân giải
- Giữ nguyên định dạng ảnh đầu ra giống với ảnh đầu vào để duy trì chất lượng