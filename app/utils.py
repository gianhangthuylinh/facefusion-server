import subprocess
import os
import uuid
import time
import math

def run_facefusion(source_path, target_path, type="image", processor="face_swapper face_enhancer"):
    """
    Chạy FaceFusion với các tham số đã cho
    """
    # Tạo thư mục kết quả nếu chưa tồn tại
    results_dir = "/app/results"
    os.makedirs(results_dir, exist_ok=True)

    # Tạo tên file đầu ra ngẫu nhiên để tránh xung đột
    output_id = str(uuid.uuid4())

    # Kiểm tra nếu target là video
    target_ext = os.path.splitext(target_path)[1].lower()
    is_video = target_ext in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"] or type == "video"

    # Cấu hình output đúng format theo loại file
    if is_video:
        output_ext = ".mp4"
    else:
        # Giữ định dạng ảnh như file target hoặc dùng png mặc định
        if target_ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            output_ext = target_ext
        else:
            output_ext = ".png"  # Mặc định output là PNG cho chất lượng tốt

    # Tạo đường dẫn đầy đủ cho file output
    final_output = os.path.join(results_dir, f"{output_id}{output_ext}")

    # Tạo lệnh FaceFusion với cú pháp mới cho FaceFusion 3.3.2
    cmd = [
        "python3", "/facefusion/facefusion.py",
        "headless-run",
        "-s", source_path,
        "-t", target_path,
        "--processors", processor,
        "--execution-providers", "cuda",
        "--execution-thread-count", "8",
        "-o", final_output,
        '--deep-swapper-morph', '100'
    ]

    # Thêm tham số tối ưu cho video
    if is_video:
        cmd.extend([
            "--output-video-encoder", "libx264",
            "--output-video-quality", "100",
        ])

    # Thực thi lệnh
    print(f"Thực thi lệnh: {' '.join(cmd)}")

    # Khởi tạo process là None
    process = None
    error_output = []

    try:
        # Sử dụng subprocess.run với streaming output
        process = subprocess.Popen(
            cmd,
            cwd="/facefusion",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Tách riêng stderr thay vì redirect vào stdout
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Đọc và in output theo thời gian thực
        print("--- Bắt đầu xử lý FaceFusion ---")
        start_time = time.time()

        while True:
            # Kiểm tra process có còn chạy không
            if process.poll() is not None:
                # Process đã kết thúc, đọc output còn lại
                remaining_stdout = process.stdout.read()
                remaining_stderr = process.stderr.read()

                if remaining_stdout:
                    for line in remaining_stdout.strip().split('\n'):
                        if line:
                            print(f"[FaceFusion] {line}")

                if remaining_stderr:
                    for line in remaining_stderr.strip().split('\n'):
                        if line:
                            print(f"[FaceFusion Error] {line}")
                            error_output.append(line)
                break

            # Đọc từ stdout
            try:
                output = process.stdout.readline()
                if output:
                    print(f"[FaceFusion] {output.strip()}")
            except:
                pass

            # Đọc từ stderr
            try:
                error = process.stderr.readline()
                if error:
                    error_line = error.strip()
                    print(f"[FaceFusion Error] {error_line}")
                    error_output.append(error_line)
            except:
                pass

        # Tính toán thời gian xử lý và làm tròn lên
        end_time = time.time()
        processing_time = end_time - start_time

        # Làm tròn lên đến số nguyên
        processing_time_rounded = math.ceil(processing_time)

        print("--- Hoàn thành xử lý FaceFusion ---")

        # Kiểm tra lỗi
        if process.returncode != 0:
            error_details = "\n".join(error_output) if error_output else "Không có thông tin lỗi chi tiết"
            cmd_str = " ".join(cmd)

            error_msg = f"""FaceFusion thất bại:
- Mã lỗi: {process.returncode}
- Lệnh đã chạy: {cmd_str}
- Chi tiết lỗi:
{error_details}"""

            raise Exception(error_msg)

        # Kiểm tra xem file đã được tạo chưa
        if not os.path.exists(final_output):
            raise Exception(f"File kết quả không được tạo tại {final_output}")

        # Kiểm tra kích thước file
        file_size = os.path.getsize(final_output)
        if file_size == 0:
            raise Exception("File kết quả có kích thước 0 bytes")

        print(f"Xử lý thành công trong {processing_time_rounded} giây (thực tế: {processing_time:.2f}s). File đầu ra: {final_output} ({file_size} bytes)")
        return final_output, processing_time_rounded

    except subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
        raise Exception("FaceFusion processing timed out (10 phút)")
    except Exception as e:
        # Dọn dẹp process nếu còn chạy
        if process is not None and process.poll() is None:
            process.kill()

        # Dọn dẹp file output nếu có lỗi
        if os.path.exists(final_output):
            try:
                os.remove(final_output)
            except:
                pass
        raise Exception(f"Lỗi khi chạy FaceFusion: {str(e)}")