from fastapi import FastAPI, UploadFile, File, Form, HTTPException, \
    BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import mimetypes
from app.utils import run_facefusion

app = FastAPI(title="FaceFusion API", version="1.0.0")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đảm bảo thư mục uploads và results tồn tại
UPLOAD_DIR = "/app/uploads"
RESULT_DIR = "/app/results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Map định dạng file sang MIME type
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
}


# Hàm xóa file tạm
def cleanup_temp_files(file_paths):
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Lỗi khi xóa file tạm {file_path}: {e}")


@app.post("/swap")
async def swap_faces(
        background_tasks: BackgroundTasks,
        source: UploadFile = File(...),
        target: UploadFile = File(...),
        type: str = Form("image"),
        processor: str = Form("face_swapper face_enhancer")
):
    temp_files = []

    try:
        # Lưu source file với đúng định dạng
        source_ext = os.path.splitext(source.filename)[
            1].lower() if source.filename else ".png"
        if not source_ext or source_ext not in [".jpg", ".jpeg", ".png",
                                                ".webp", ".bmp"]:
            source_ext = ".png"  # Mặc định là png nếu không xác định được

        source_path = os.path.join(UPLOAD_DIR,
                                   f"source_{uuid.uuid4()}{source_ext}")
        temp_files.append(source_path)

        # Lưu target file với đúng định dạng
        target_ext = os.path.splitext(target.filename)[
            1].lower() if target.filename else ".jpg"
        # Nếu type là video nhưng định dạng không phải video, thông báo lỗi
        if type == "video" and target_ext not in [".mp4", ".avi", ".mov",
                                                  ".webm", ".mkv", ".flv"]:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Định dạng file {target_ext} không hỗ trợ cho video. Vui lòng sử dụng MP4, AVI, MOV, WEBM, MKV hoặc FLV."}
            )
        # Nếu không xác định được định dạng
        if not target_ext:
            target_ext = ".mp4" if type == "video" else ".png"

        target_path = os.path.join(UPLOAD_DIR,
                                   f"target_{uuid.uuid4()}{target_ext}")
        temp_files.append(target_path)

        # Ghi file
        with open(source_path, "wb") as f:
            f.write(await source.read())
        with open(target_path, "wb") as f:
            f.write(await target.read())

        # Xử lý face swap
        output_path, processing_time_rounded = run_facefusion(source_path, target_path, type, processor)

        # Thêm output_path vào danh sách file cần xóa
        temp_files.append(output_path)

        # Lên lịch xóa file tạm sau khi response hoàn tất
        background_tasks.add_task(cleanup_temp_files, temp_files)

        # Xác định định dạng file đầu ra
        output_ext = os.path.splitext(output_path)[1].lower()
        output_mime = MIME_TYPES.get(output_ext, "application/octet-stream")

        # Đặt tên file kết quả
        if type == "video" or output_ext in [".mp4", ".avi", ".mov", ".webm", ".mkv"]:
            output_filename = f"result{output_ext}"
        else:
            output_filename = f"result{output_ext}"

        headers = {
            "X-Processing-Time": str(processing_time_rounded),
            "Access-Control-Expose-Headers": "X-Processing-Time, X-Processing-Time-Text"  # Cho phép frontend đọc headers
        }

        # Trả về file kết quả
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type=output_mime,
            background=background_tasks,
            headers=headers,
        )
    except Exception as e:
        # Đảm bảo xóa file tạm trong trường hợp lỗi
        background_tasks.add_task(cleanup_temp_files, temp_files)

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/")
async def root():
    return {
        "message": "FaceFusion API hoạt động, sử dụng /swap endpoint để hoán đổi khuôn mặt"}
